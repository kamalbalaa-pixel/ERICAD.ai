using System;
using System.Threading.Tasks;
using System.Windows;
using Frontend.Data;
using Frontend.Models;

namespace Frontend.Services
{
    /// <summary>
    /// Service that combines UI Automation with Highlight Overlay for visual guides
    /// </summary>
    public class VisualGuideService
    {
        private readonly UIAutomationService _uiService;
        private readonly HighlightOverlayService _highlightService;

        public VisualGuideService()
        {
            _uiService = new UIAutomationService();
            _highlightService = new HighlightOverlayService();
        }

        /// <summary>
        /// Checks if SolidWorks is running
        /// </summary>
        public bool IsSolidWorksRunning()
        {
            return _uiService.IsSolidWorksRunning();
        }

        /// <summary>
        /// Highlights a command by name
        /// </summary>
        /// <param name="commandName">The command to highlight (e.g., "Extrude", "Sketch", "Fillet")</param>
        /// <returns>True if element was found and highlighted</returns>
        public bool HighlightCommand(string commandName)
        {
            // Look up in hardcoded map
            var element = SolidWorksUIMap.FindByName(commandName);

            if (element == null)
            {
                return false; // Unknown command
            }

            return HighlightElement(element);
        }

        /// <summary>
        /// Highlights a specific SolidWorks UI element
        /// </summary>
        public bool HighlightElement(SolidWorksUIElement element)
        {
            // Find actual screen position using UI Automation
            var bounds = _uiService.FindElement(element);

            if (bounds.HasValue)
            {
                // Determine arrow direction based on element location
                var arrowDir = DetermineArrowDirection(bounds.Value);

                // Show highlight with label
                string label = $"Click: {element.CommandName}";
                if (!string.IsNullOrEmpty(element.Shortcut))
                {
                    label += $" (or press {element.Shortcut})";
                }

                _highlightService.HighlightWithArrow(bounds.Value, label, arrowDir);
                return true;
            }

            return false;
        }

        /// <summary>
        /// Highlights a region at specific screen coordinates
        /// </summary>
        public void HighlightRegion(Rect region, string? label = null)
        {
            _highlightService.HighlightRegion(region, label);
        }

        /// <summary>
        /// Clears all highlights
        /// </summary>
        public void ClearHighlights()
        {
            _highlightService.ClearHighlights();
        }

        /// <summary>
        /// Hides the overlay
        /// </summary>
        public void Hide()
        {
            _highlightService.Hide();
        }

        /// <summary>
        /// Shows the overlay
        /// </summary>
        public void Show()
        {
            _highlightService.Show();
        }

        /// <summary>
        /// Closes and cleans up
        /// </summary>
        public void Dispose()
        {
            _highlightService.Close();
        }

        private ArrowDirection DetermineArrowDirection(Rect elementBounds)
        {
            // Get screen dimensions
            double screenWidth = SystemParameters.PrimaryScreenWidth;
            double screenHeight = SystemParameters.PrimaryScreenHeight;

            double centerX = elementBounds.X + elementBounds.Width / 2;
            double centerY = elementBounds.Y + elementBounds.Height / 2;

            // Choose arrow direction based on element position
            // If element is on the left side of screen, arrow comes from left
            // If element is on the right side, arrow comes from right
            // etc.

            if (centerX < screenWidth / 3)
            {
                return ArrowDirection.Left;
            }
            else if (centerX > screenWidth * 2 / 3)
            {
                return ArrowDirection.Right;
            }
            else if (centerY < screenHeight / 3)
            {
                return ArrowDirection.Top;
            }
            else
            {
                return ArrowDirection.Bottom;
            }
        }

        /// <summary>
        /// Dumps the SolidWorks UI tree for discovery purposes
        /// </summary>
        public void DumpUITree(string outputPath)
        {
            _uiService.DumpUITree(outputPath);
        }

        /// <summary>
        /// Gets all buttons in SolidWorks
        /// </summary>
        public System.Collections.Generic.List<DiscoveredElement> GetAllButtons()
        {
            return _uiService.GetAllButtons();
        }

        /// <summary>
        /// Gets all menu items in SolidWorks
        /// </summary>
        public System.Collections.Generic.List<DiscoveredElement> GetAllMenuItems()
        {
            return _uiService.GetAllMenuItems();
        }
    }
}

