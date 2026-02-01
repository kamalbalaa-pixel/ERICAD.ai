using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows;
using System.Windows.Automation;
using Condition = System.Windows.Automation.Condition;
using Frontend.Models;

namespace Frontend.Services
{
    /// <summary>
    /// Service for finding UI elements in SolidWorks using Windows UI Automation
    /// </summary>
    public class UIAutomationService
    {
        private AutomationElement? _solidWorksRoot;
        private IntPtr _solidWorksHandle;

        #region Win32 Imports

        [DllImport("user32.dll")]
        private static extern IntPtr FindWindow(string? lpClassName, string? lpWindowName);

        [DllImport("user32.dll")]
        private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

        private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        [DllImport("user32.dll", CharSet = CharSet.Auto)]
        private static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

        [DllImport("user32.dll")]
        private static extern bool IsWindowVisible(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        [StructLayout(LayoutKind.Sequential)]
        public struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }

        #endregion

        /// <summary>
        /// Attempts to connect to the SolidWorks application window
        /// </summary>
        public bool ConnectToSolidWorks()
        {
            _solidWorksHandle = FindSolidWorksWindow();

            if (_solidWorksHandle == IntPtr.Zero)
            {
                return false;
            }

            try
            {
                _solidWorksRoot = AutomationElement.FromHandle(_solidWorksHandle);
                return _solidWorksRoot != null;
            }
            catch (Exception)
            {
                return false;
            }
        }

        /// <summary>
        /// Checks if SolidWorks is currently running and accessible
        /// </summary>
        public bool IsSolidWorksRunning()
        {
            var hwnd = FindSolidWorksWindow();
            return hwnd != IntPtr.Zero;
        }

        /// <summary>
        /// Gets the SolidWorks window bounds
        /// </summary>
        public Rect? GetSolidWorksWindowBounds()
        {
            if (_solidWorksHandle == IntPtr.Zero)
            {
                ConnectToSolidWorks();
            }

            if (_solidWorksHandle == IntPtr.Zero)
                return null;

            if (GetWindowRect(_solidWorksHandle, out RECT rect))
            {
                return new Rect(rect.Left, rect.Top, rect.Right - rect.Left, rect.Bottom - rect.Top);
            }

            return null;
        }

        private IntPtr FindSolidWorksWindow()
        {
            IntPtr foundWindow = IntPtr.Zero;

            EnumWindows((hwnd, lParam) =>
            {
                if (!IsWindowVisible(hwnd))
                    return true; // Continue enumeration

                StringBuilder title = new StringBuilder(256);
                GetWindowText(hwnd, title, 256);

                string windowTitle = title.ToString();

                // SolidWorks window titles usually contain "SOLIDWORKS"
                if (windowTitle.Contains("SOLIDWORKS", StringComparison.OrdinalIgnoreCase))
                {
                    foundWindow = hwnd;
                    return false; // Stop enumeration
                }

                return true; // Continue enumeration
            }, IntPtr.Zero);

            return foundWindow;
        }

        /// <summary>
        /// Finds a UI element based on the SolidWorks element definition
        /// </summary>
        public Rect? FindElement(SolidWorksUIElement element)
        {
            if (_solidWorksRoot == null)
            {
                if (!ConnectToSolidWorks())
                    return null;
            }

            try
            {
                AutomationElement? found = null;

                // Strategy 1: Search by AutomationId (most reliable)
                if (!string.IsNullOrEmpty(element.AutomationId))
                {
                    found = FindByAutomationId(element.AutomationId);
                }

                // Strategy 2: Search by Name and ControlType
                if (found == null && !string.IsNullOrEmpty(element.Name))
                {
                    found = FindByName(element.Name, element.ControlType);
                }

                // Strategy 3: Search by path through UI tree
                if (found == null && element.SearchPath != null && element.SearchPath.Length > 0)
                {
                    found = FindByPath(element.SearchPath);
                }

                // Strategy 4: Partial name match (for dynamic names)
                if (found == null && !string.IsNullOrEmpty(element.Name))
                {
                    found = FindByPartialName(element.Name, element.ControlType);
                }

                if (found != null)
                {
                    Rect bounds = found.Current.BoundingRectangle;

                    // Validate bounds are on screen
                    if (bounds.Width > 0 && bounds.Height > 0 &&
                        !double.IsInfinity(bounds.X) && !double.IsInfinity(bounds.Y))
                    {
                        return bounds;
                    }
                }
            }
            catch (ElementNotAvailableException)
            {
                // Element disappeared, refresh connection
                _solidWorksRoot = null;
            }
            catch (Exception)
            {
                // Silently handle other errors
            }

            return null;
        }

        /// <summary>
        /// Finds element by AutomationId property
        /// </summary>
        private AutomationElement? FindByAutomationId(string automationId)
        {
            if (_solidWorksRoot == null) return null;

            var condition = new PropertyCondition(
                AutomationElement.AutomationIdProperty,
                automationId
            );

            return _solidWorksRoot.FindFirst(TreeScope.Descendants, condition);
        }

        /// <summary>
        /// Finds element by exact Name and ControlType
        /// </summary>
        private AutomationElement? FindByName(string name, ControlType? controlType)
        {
            if (_solidWorksRoot == null) return null;

            Condition condition;

            if (controlType != null)
            {
                condition = new AndCondition(
                    new PropertyCondition(AutomationElement.NameProperty, name),
                    new PropertyCondition(AutomationElement.ControlTypeProperty, controlType)
                );
            }
            else
            {
                condition = new PropertyCondition(AutomationElement.NameProperty, name);
            }

            return _solidWorksRoot.FindFirst(TreeScope.Descendants, condition);
        }

        /// <summary>
        /// Finds element by partial name match
        /// </summary>
        private AutomationElement? FindByPartialName(string partialName, ControlType? controlType)
        {
            if (_solidWorksRoot == null) return null;

            Condition baseCondition = controlType != null
                ? new PropertyCondition(AutomationElement.ControlTypeProperty, controlType)
                : Condition.TrueCondition;

            var elements = _solidWorksRoot.FindAll(TreeScope.Descendants, baseCondition);

            foreach (AutomationElement element in elements)
            {
                try
                {
                    string elementName = element.Current.Name;
                    if (!string.IsNullOrEmpty(elementName) &&
                        elementName.Contains(partialName, StringComparison.OrdinalIgnoreCase))
                    {
                        return element;
                    }
                }
                catch
                {
                    // Skip elements that throw exceptions
                }
            }

            return null;
        }

        /// <summary>
        /// Finds element by walking through the UI tree path
        /// </summary>
        private AutomationElement? FindByPath(string[] path)
        {
            if (_solidWorksRoot == null) return null;

            AutomationElement current = _solidWorksRoot;

            foreach (string pathPart in path)
            {
                var condition = new PropertyCondition(AutomationElement.NameProperty, pathPart);
                var found = current.FindFirst(TreeScope.Children, condition);

                if (found == null)
                {
                    // Try descendants if not found in children
                    found = current.FindFirst(TreeScope.Descendants, condition);
                }

                if (found == null)
                    return null;

                current = found;
            }

            return current;
        }

        /// <summary>
        /// Dumps the entire UI tree of SolidWorks to a file for analysis
        /// Use this to discover element properties for mapping
        /// </summary>
        public void DumpUITree(string outputPath)
        {
            if (_solidWorksRoot == null)
            {
                if (!ConnectToSolidWorks())
                {
                    File.WriteAllText(outputPath, "ERROR: Could not connect to SolidWorks. Make sure it is running.");
                    return;
                }
            }

            var sb = new StringBuilder();
            sb.AppendLine("=== SOLIDWORKS UI TREE DUMP ===");
            sb.AppendLine($"Generated: {DateTime.Now}");
            sb.AppendLine($"Window Handle: {_solidWorksHandle}");
            sb.AppendLine("================================\n");

            DumpElement(_solidWorksRoot!, sb, 0, 3); // Limit depth to 3 for performance

            File.WriteAllText(outputPath, sb.ToString());
        }

        /// <summary>
        /// Dumps UI tree with full depth (WARNING: Can be slow!)
        /// </summary>
        public void DumpUITreeFull(string outputPath, int maxDepth = 5)
        {
            if (_solidWorksRoot == null)
            {
                if (!ConnectToSolidWorks())
                {
                    File.WriteAllText(outputPath, "ERROR: Could not connect to SolidWorks.");
                    return;
                }
            }

            var sb = new StringBuilder();
            sb.AppendLine("=== SOLIDWORKS FULL UI TREE DUMP ===");
            sb.AppendLine($"Generated: {DateTime.Now}");
            sb.AppendLine($"Max Depth: {maxDepth}");
            sb.AppendLine("====================================\n");

            DumpElement(_solidWorksRoot!, sb, 0, maxDepth);

            File.WriteAllText(outputPath, sb.ToString());
        }

        private void DumpElement(AutomationElement element, StringBuilder sb, int indent, int maxDepth)
        {
            if (indent > maxDepth) return;

            string indentStr = new string(' ', indent * 2);

            try
            {
                var current = element.Current;

                sb.AppendLine($"{indentStr}┌─ Name: \"{current.Name}\"");
                sb.AppendLine($"{indentStr}│  AutomationId: \"{current.AutomationId}\"");
                sb.AppendLine($"{indentStr}│  ClassName: \"{current.ClassName}\"");
                sb.AppendLine($"{indentStr}│  ControlType: {current.ControlType.ProgrammaticName}");
                sb.AppendLine($"{indentStr}│  BoundingRect: X={current.BoundingRectangle.X:F0}, Y={current.BoundingRectangle.Y:F0}, W={current.BoundingRectangle.Width:F0}, H={current.BoundingRectangle.Height:F0}");
                sb.AppendLine($"{indentStr}│  IsEnabled: {current.IsEnabled}");
                sb.AppendLine($"{indentStr}└──────────────────────────────");

                var children = element.FindAll(TreeScope.Children, Condition.TrueCondition);
                foreach (AutomationElement child in children)
                {
                    DumpElement(child, sb, indent + 1, maxDepth);
                }
            }
            catch (Exception ex)
            {
                sb.AppendLine($"{indentStr}[ERROR: {ex.Message}]");
            }
        }

        /// <summary>
        /// Gets all buttons in SolidWorks for quick reference
        /// </summary>
        public List<DiscoveredElement> GetAllButtons()
        {
            var buttons = new List<DiscoveredElement>();

            if (_solidWorksRoot == null)
            {
                if (!ConnectToSolidWorks())
                    return buttons;
            }

            try
            {
                var condition = new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.Button);
                var elements = _solidWorksRoot!.FindAll(TreeScope.Descendants, condition);

                foreach (AutomationElement element in elements)
                {
                    try
                    {
                        var current = element.Current;
                        if (!string.IsNullOrWhiteSpace(current.Name))
                        {
                            buttons.Add(new DiscoveredElement
                            {
                                Name = current.Name,
                                AutomationId = current.AutomationId,
                                ClassName = current.ClassName,
                                ControlType = current.ControlType.ProgrammaticName,
                                Bounds = current.BoundingRectangle
                            });
                        }
                    }
                    catch
                    {
                        // Skip elements that throw
                    }
                }
            }
            catch
            {
                // Return what we have
            }

            return buttons;
        }

        /// <summary>
        /// Gets all menu items in SolidWorks
        /// </summary>
        public List<DiscoveredElement> GetAllMenuItems()
        {
            var items = new List<DiscoveredElement>();

            if (_solidWorksRoot == null)
            {
                if (!ConnectToSolidWorks())
                    return items;
            }

            try
            {
                var condition = new PropertyCondition(AutomationElement.ControlTypeProperty, ControlType.MenuItem);
                var elements = _solidWorksRoot!.FindAll(TreeScope.Descendants, condition);

                foreach (AutomationElement element in elements)
                {
                    try
                    {
                        var current = element.Current;
                        if (!string.IsNullOrWhiteSpace(current.Name))
                        {
                            items.Add(new DiscoveredElement
                            {
                                Name = current.Name,
                                AutomationId = current.AutomationId,
                                ClassName = current.ClassName,
                                ControlType = current.ControlType.ProgrammaticName,
                                Bounds = current.BoundingRectangle
                            });
                        }
                    }
                    catch
                    {
                        // Skip elements that throw
                    }
                }
            }
            catch
            {
                // Return what we have
            }

            return items;
        }
    }

    /// <summary>
    /// Represents a UI element discovered during analysis
    /// </summary>
    public class DiscoveredElement
    {
        public string Name { get; set; } = "";
        public string AutomationId { get; set; } = "";
        public string ClassName { get; set; } = "";
        public string ControlType { get; set; } = "";
        public Rect Bounds { get; set; }
    }
}

