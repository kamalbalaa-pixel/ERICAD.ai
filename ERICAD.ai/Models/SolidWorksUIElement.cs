using System.Windows.Automation;

namespace Frontend.Models
{
    /// <summary>
    /// Represents a UI element in SolidWorks that can be highlighted
    /// </summary>
    public class SolidWorksUIElement
    {
        /// <summary>
        /// The command name (e.g., "Extrude", "Sketch", "Fillet")
        /// </summary>
        public string CommandName { get; set; } = "";

        /// <summary>
        /// UI Automation ID - most reliable way to find elements
        /// </summary>
        public string AutomationId { get; set; } = "";

        /// <summary>
        /// Display name of the element
        /// </summary>
        public string Name { get; set; } = "";

        /// <summary>
        /// Window class name (e.g., "AfxWnd140u")
        /// </summary>
        public string ClassName { get; set; } = "";

        /// <summary>
        /// Path through the UI tree to find this element
        /// </summary>
        public string[]? SearchPath { get; set; }

        /// <summary>
        /// The type of control (Button, MenuItem, etc.)
        /// </summary>
        public ControlType? ControlType { get; set; }

        /// <summary>
        /// Description for users/AI
        /// </summary>
        public string Description { get; set; } = "";

        /// <summary>
        /// Alternative names that might be used (e.g., "Boss Extrude", "Extrude Boss/Base")
        /// </summary>
        public string[]? AlternateNames { get; set; }

        /// <summary>
        /// Keyboard shortcut if available
        /// </summary>
        public string? Shortcut { get; set; }

        /// <summary>
        /// Category for grouping (Sketch, Features, Assembly, etc.)
        /// </summary>
        public string Category { get; set; } = "General";
    }
}

