using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Automation;
using Frontend.Models;

namespace Frontend.Data
{
    /// <summary>
    /// Hardcoded mapping of SolidWorks UI elements
    /// NOTE: You need to run the UIDiscoveryTool to find the actual AutomationIds
    /// and Names for your version of SolidWorks, then update this file.
    /// </summary>
    public static class SolidWorksUIMap
    {
        /// <summary>
        /// Dictionary of all known SolidWorks UI elements
        /// Key is a normalized lowercase identifier
        /// </summary>
        public static readonly Dictionary<string, SolidWorksUIElement> Elements = new()
        {
            // ============================================
            // SKETCH TAB - Drawing tools
            // ============================================
            ["sketch"] = new SolidWorksUIElement
            {
                CommandName = "Sketch",
                AutomationId = "", // Fill in after discovery
                Name = "Sketch",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Sketch" },
                Description = "Start a new sketch on a plane or face",
                AlternateNames = new[] { "New Sketch", "Create Sketch", "2D Sketch" },
                Shortcut = "S",
                Category = "Sketch"
            },

            ["line"] = new SolidWorksUIElement
            {
                CommandName = "Line",
                AutomationId = "",
                Name = "Line",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Sketch", "Line" },
                Description = "Draw a line in sketch mode",
                AlternateNames = new[] { "Sketch Line" },
                Shortcut = "L",
                Category = "Sketch"
            },

            ["rectangle"] = new SolidWorksUIElement
            {
                CommandName = "Corner Rectangle",
                AutomationId = "",
                Name = "Corner Rectangle",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Sketch", "Rectangle" },
                Description = "Draw a rectangle by corner points",
                AlternateNames = new[] { "Rectangle", "Box" },
                Shortcut = "R",
                Category = "Sketch"
            },

            ["circle"] = new SolidWorksUIElement
            {
                CommandName = "Circle",
                AutomationId = "",
                Name = "Circle",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Sketch", "Circle" },
                Description = "Draw a circle by center and radius",
                AlternateNames = new[] { "Sketch Circle" },
                Shortcut = "C",
                Category = "Sketch"
            },

            ["arc"] = new SolidWorksUIElement
            {
                CommandName = "Centerpoint Arc",
                AutomationId = "",
                Name = "Centerpoint Arc",
                ControlType = ControlType.Button,
                Description = "Draw an arc from center point",
                AlternateNames = new[] { "Arc", "3 Point Arc" },
                Shortcut = "A",
                Category = "Sketch"
            },

            ["smartdimension"] = new SolidWorksUIElement
            {
                CommandName = "Smart Dimension",
                AutomationId = "",
                Name = "Smart Dimension",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Sketch", "Smart Dimension" },
                Description = "Add dimensions to sketch entities",
                AlternateNames = new[] { "Dimension", "Add Dimension" },
                Shortcut = "D",
                Category = "Sketch"
            },

            ["trim"] = new SolidWorksUIElement
            {
                CommandName = "Trim Entities",
                AutomationId = "",
                Name = "Trim Entities",
                ControlType = ControlType.Button,
                Description = "Trim sketch entities",
                AlternateNames = new[] { "Trim", "Power Trim" },
                Shortcut = "T",
                Category = "Sketch"
            },

            ["mirror"] = new SolidWorksUIElement
            {
                CommandName = "Mirror Entities",
                AutomationId = "",
                Name = "Mirror Entities",
                ControlType = ControlType.Button,
                Description = "Mirror sketch entities",
                AlternateNames = new[] { "Mirror", "Sketch Mirror" },
                Category = "Sketch"
            },

            ["offset"] = new SolidWorksUIElement
            {
                CommandName = "Offset Entities",
                AutomationId = "",
                Name = "Offset Entities",
                ControlType = ControlType.Button,
                Description = "Offset sketch entities by a distance",
                AlternateNames = new[] { "Offset", "Offset Curve" },
                Shortcut = "O",
                Category = "Sketch"
            },

            ["exitsketch"] = new SolidWorksUIElement
            {
                CommandName = "Exit Sketch",
                AutomationId = "",
                Name = "Exit Sketch",
                ControlType = ControlType.Button,
                Description = "Exit the current sketch",
                AlternateNames = new[] { "Close Sketch", "Finish Sketch" },
                Category = "Sketch"
            },

            // ============================================
            // FEATURES TAB - 3D modeling tools
            // ============================================
            ["extrudeboss"] = new SolidWorksUIElement
            {
                CommandName = "Extruded Boss/Base",
                AutomationId = "",
                Name = "Extruded Boss/Base",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Features", "Extruded Boss/Base" },
                Description = "Create an extruded boss or base feature from a sketch",
                AlternateNames = new[] { "Extrude", "Boss Extrude", "Extrusion" },
                Shortcut = "E",
                Category = "Features"
            },

            ["extrudecut"] = new SolidWorksUIElement
            {
                CommandName = "Extruded Cut",
                AutomationId = "",
                Name = "Extruded Cut",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Features", "Extruded Cut" },
                Description = "Create an extruded cut feature to remove material",
                AlternateNames = new[] { "Cut Extrude", "Cut" },
                Category = "Features"
            },

            ["revolveboss"] = new SolidWorksUIElement
            {
                CommandName = "Revolved Boss/Base",
                AutomationId = "",
                Name = "Revolved Boss/Base",
                ControlType = ControlType.Button,
                Description = "Create a revolved feature from a sketch",
                AlternateNames = new[] { "Revolve", "Revolution" },
                Category = "Features"
            },

            ["revolvecut"] = new SolidWorksUIElement
            {
                CommandName = "Revolved Cut",
                AutomationId = "",
                Name = "Revolved Cut",
                ControlType = ControlType.Button,
                Description = "Create a revolved cut to remove material",
                AlternateNames = new[] { "Cut Revolve" },
                Category = "Features"
            },

            ["fillet"] = new SolidWorksUIElement
            {
                CommandName = "Fillet",
                AutomationId = "",
                Name = "Fillet",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Features", "Fillet" },
                Description = "Add rounded edges (fillets) to edges",
                AlternateNames = new[] { "Round", "Edge Fillet" },
                Category = "Features"
            },

            ["chamfer"] = new SolidWorksUIElement
            {
                CommandName = "Chamfer",
                AutomationId = "",
                Name = "Chamfer",
                ControlType = ControlType.Button,
                SearchPath = new[] { "CommandManager", "Features", "Chamfer" },
                Description = "Add beveled edges (chamfers) to edges",
                AlternateNames = new[] { "Bevel" },
                Category = "Features"
            },

            ["hole"] = new SolidWorksUIElement
            {
                CommandName = "Hole Wizard",
                AutomationId = "",
                Name = "Hole Wizard",
                ControlType = ControlType.Button,
                Description = "Create standard holes using the hole wizard",
                AlternateNames = new[] { "Hole", "Drill Hole", "Add Hole" },
                Category = "Features"
            },

            ["shell"] = new SolidWorksUIElement
            {
                CommandName = "Shell",
                AutomationId = "",
                Name = "Shell",
                ControlType = ControlType.Button,
                Description = "Hollow out a solid body",
                AlternateNames = new[] { "Hollow", "Thin Wall" },
                Category = "Features"
            },

            ["linearpattern"] = new SolidWorksUIElement
            {
                CommandName = "Linear Pattern",
                AutomationId = "",
                Name = "Linear Pattern",
                ControlType = ControlType.Button,
                Description = "Create a linear array of features",
                AlternateNames = new[] { "Pattern", "Array" },
                Category = "Features"
            },

            ["circularpattern"] = new SolidWorksUIElement
            {
                CommandName = "Circular Pattern",
                AutomationId = "",
                Name = "Circular Pattern",
                ControlType = ControlType.Button,
                Description = "Create a circular array of features",
                AlternateNames = new[] { "Radial Pattern", "Polar Pattern" },
                Category = "Features"
            },

            ["mirrorfeature"] = new SolidWorksUIElement
            {
                CommandName = "Mirror",
                AutomationId = "",
                Name = "Mirror",
                ControlType = ControlType.Button,
                Description = "Mirror features about a plane",
                AlternateNames = new[] { "Mirror Feature", "Mirror Body" },
                Category = "Features"
            },

            ["loft"] = new SolidWorksUIElement
            {
                CommandName = "Lofted Boss/Base",
                AutomationId = "",
                Name = "Lofted Boss/Base",
                ControlType = ControlType.Button,
                Description = "Create a loft between profiles",
                AlternateNames = new[] { "Loft", "Lofted Feature" },
                Category = "Features"
            },

            ["sweep"] = new SolidWorksUIElement
            {
                CommandName = "Swept Boss/Base",
                AutomationId = "",
                Name = "Swept Boss/Base",
                ControlType = ControlType.Button,
                Description = "Create a sweep along a path",
                AlternateNames = new[] { "Sweep", "Swept Feature" },
                Category = "Features"
            },

            // ============================================
            // REFERENCE GEOMETRY
            // ============================================
            ["plane"] = new SolidWorksUIElement
            {
                CommandName = "Plane",
                AutomationId = "",
                Name = "Plane",
                ControlType = ControlType.Button,
                Description = "Create a reference plane",
                AlternateNames = new[] { "Reference Plane", "New Plane" },
                Category = "Reference Geometry"
            },

            ["axis"] = new SolidWorksUIElement
            {
                CommandName = "Axis",
                AutomationId = "",
                Name = "Axis",
                ControlType = ControlType.Button,
                Description = "Create a reference axis",
                AlternateNames = new[] { "Reference Axis" },
                Category = "Reference Geometry"
            },

            // ============================================
            // FEATURE MANAGER / DESIGN TREE
            // ============================================
            ["frontplane"] = new SolidWorksUIElement
            {
                CommandName = "Front Plane",
                AutomationId = "",
                Name = "Front Plane",
                ControlType = ControlType.TreeItem,
                Description = "The front reference plane in the FeatureManager",
                AlternateNames = new[] { "Front" },
                Category = "FeatureManager"
            },

            ["topplane"] = new SolidWorksUIElement
            {
                CommandName = "Top Plane",
                AutomationId = "",
                Name = "Top Plane",
                ControlType = ControlType.TreeItem,
                Description = "The top reference plane in the FeatureManager",
                AlternateNames = new[] { "Top" },
                Category = "FeatureManager"
            },

            ["rightplane"] = new SolidWorksUIElement
            {
                CommandName = "Right Plane",
                AutomationId = "",
                Name = "Right Plane",
                ControlType = ControlType.TreeItem,
                Description = "The right reference plane in the FeatureManager",
                AlternateNames = new[] { "Right" },
                Category = "FeatureManager"
            },

            ["origin"] = new SolidWorksUIElement
            {
                CommandName = "Origin",
                AutomationId = "",
                Name = "Origin",
                ControlType = ControlType.TreeItem,
                Description = "The origin point in the FeatureManager",
                Category = "FeatureManager"
            },

            // ============================================
            // PROPERTY MANAGER (Confirmation buttons)
            // ============================================
            ["ok"] = new SolidWorksUIElement
            {
                CommandName = "OK",
                AutomationId = "",
                Name = "OK",
                ControlType = ControlType.Button,
                SearchPath = new[] { "PropertyManager", "OK" },
                Description = "Confirm the current operation",
                AlternateNames = new[] { "Confirm", "Accept", "Green Check" },
                Category = "PropertyManager"
            },

            ["cancel"] = new SolidWorksUIElement
            {
                CommandName = "Cancel",
                AutomationId = "",
                Name = "Cancel",
                ControlType = ControlType.Button,
                SearchPath = new[] { "PropertyManager", "Cancel" },
                Description = "Cancel the current operation",
                AlternateNames = new[] { "Red X", "Close" },
                Shortcut = "Escape",
                Category = "PropertyManager"
            },

            // ============================================
            // FILE MENU
            // ============================================
            ["filemenu"] = new SolidWorksUIElement
            {
                CommandName = "File Menu",
                AutomationId = "",
                Name = "File",
                ControlType = ControlType.MenuItem,
                SearchPath = new[] { "Menu Bar", "File" },
                Description = "Open the File menu",
                Category = "Menu"
            },

            ["new"] = new SolidWorksUIElement
            {
                CommandName = "New",
                AutomationId = "",
                Name = "New",
                ControlType = ControlType.MenuItem,
                Description = "Create a new document",
                AlternateNames = new[] { "New Document", "New File" },
                Shortcut = "Ctrl+N",
                Category = "Menu"
            },

            ["open"] = new SolidWorksUIElement
            {
                CommandName = "Open",
                AutomationId = "",
                Name = "Open",
                ControlType = ControlType.MenuItem,
                Description = "Open an existing document",
                AlternateNames = new[] { "Open File" },
                Shortcut = "Ctrl+O",
                Category = "Menu"
            },

            ["save"] = new SolidWorksUIElement
            {
                CommandName = "Save",
                AutomationId = "",
                Name = "Save",
                ControlType = ControlType.MenuItem,
                Description = "Save the current document",
                AlternateNames = new[] { "Save File" },
                Shortcut = "Ctrl+S",
                Category = "Menu"
            },

            // ============================================
            // VIEW CONTROLS
            // ============================================
            ["zoomtofit"] = new SolidWorksUIElement
            {
                CommandName = "Zoom to Fit",
                AutomationId = "",
                Name = "Zoom to Fit",
                ControlType = ControlType.Button,
                Description = "Fit the entire model in the view",
                AlternateNames = new[] { "Fit All", "Zoom Fit" },
                Shortcut = "F",
                Category = "View"
            },

            ["isometric"] = new SolidWorksUIElement
            {
                CommandName = "Isometric",
                AutomationId = "",
                Name = "Isometric",
                ControlType = ControlType.Button,
                Description = "Set view to isometric orientation",
                AlternateNames = new[] { "Iso View" },
                Category = "View"
            },

            ["trimetric"] = new SolidWorksUIElement
            {
                CommandName = "Trimetric",
                AutomationId = "",
                Name = "Trimetric",
                ControlType = ControlType.Button,
                Description = "Set view to trimetric orientation",
                Category = "View"
            },

            // ============================================
            // MATE COMMANDS (Assembly)
            // ============================================
            ["mate"] = new SolidWorksUIElement
            {
                CommandName = "Mate",
                AutomationId = "",
                Name = "Mate",
                ControlType = ControlType.Button,
                Description = "Add a mate between components",
                AlternateNames = new[] { "Add Mate", "Constraint" },
                Category = "Assembly"
            },

            ["insertcomponent"] = new SolidWorksUIElement
            {
                CommandName = "Insert Component",
                AutomationId = "",
                Name = "Insert Component",
                ControlType = ControlType.Button,
                Description = "Insert a component into the assembly",
                AlternateNames = new[] { "Add Part", "Insert Part" },
                Category = "Assembly"
            },

            // ============================================
            // MEASURE & ANALYSIS
            // ============================================
            ["measure"] = new SolidWorksUIElement
            {
                CommandName = "Measure",
                AutomationId = "Item 33068",  // ✅ DISCOVERED
                Name = "Measure",
                ControlType = ControlType.Button,
                Description = "Measure distances, angles, and other properties",
                AlternateNames = new[] { "Measure Tool", "Measurement" },
                Category = "Evaluate"
            },

            ["massproperties"] = new SolidWorksUIElement
            {
                CommandName = "Mass Properties",
                AutomationId = "Item 34125",  // ✅ DISCOVERED
                Name = "Mass Properties",
                ControlType = ControlType.Button,
                Description = "Calculate mass, volume, and other properties",
                AlternateNames = new[] { "Mass", "Properties" },
                Category = "Evaluate"
            },

            // ============================================
            // ANNOTATION TOOLBAR (Discovered from UI dump)
            // ============================================
            ["note"] = new SolidWorksUIElement
            {
                CommandName = "Note",
                AutomationId = "Item 32851",  // ✅ DISCOVERED
                Name = "Note",
                ControlType = ControlType.Button,
                Description = "Add a note annotation",
                Category = "Annotation"
            },

            ["balloon"] = new SolidWorksUIElement
            {
                CommandName = "Balloon",
                AutomationId = "Item 32852",  // ✅ DISCOVERED
                Name = "Balloon",
                ControlType = ControlType.Button,
                Description = "Add a balloon annotation",
                Category = "Annotation"
            },

            ["surfacefinish"] = new SolidWorksUIElement
            {
                CommandName = "Surface Finish",
                AutomationId = "Item 33113",  // ✅ DISCOVERED
                Name = "Surface Finish",
                ControlType = ControlType.Button,
                Description = "Add surface finish symbol",
                Category = "Annotation"
            },

            ["weldsymbol"] = new SolidWorksUIElement
            {
                CommandName = "Weld Symbol",
                AutomationId = "Item 33301",  // ✅ DISCOVERED
                Name = "Weld Symbol",
                ControlType = ControlType.Button,
                Description = "Add weld symbol annotation",
                Category = "Annotation"
            },

            ["geometrictolerance"] = new SolidWorksUIElement
            {
                CommandName = "Geometric Tolerance",
                AutomationId = "Item 32925",  // ✅ DISCOVERED
                Name = "Geometric Tolerance",
                ControlType = ControlType.Button,
                Description = "Add geometric tolerance annotation",
                AlternateNames = new[] { "GD&T" },
                Category = "Annotation"
            },

            ["datumfeature"] = new SolidWorksUIElement
            {
                CommandName = "Datum Feature",
                AutomationId = "Item 33125",  // ✅ DISCOVERED
                Name = "Datum Feature",
                ControlType = ControlType.Button,
                Description = "Add datum feature symbol",
                Category = "Annotation"
            },

            ["holecallout"] = new SolidWorksUIElement
            {
                CommandName = "Hole Callout",
                AutomationId = "Item 33171",  // ✅ DISCOVERED
                Name = "Hole Callout",
                ControlType = ControlType.Button,
                Description = "Add hole callout annotation",
                Category = "Annotation"
            },

            ["centermark"] = new SolidWorksUIElement
            {
                CommandName = "Center Mark",
                AutomationId = "Item 33085",  // ✅ DISCOVERED
                Name = "Center Mark",
                ControlType = ControlType.Button,
                Description = "Add center mark annotation",
                Category = "Annotation"
            },

            ["centerline"] = new SolidWorksUIElement
            {
                CommandName = "Centerline",
                AutomationId = "Item 38115",  // ✅ DISCOVERED
                Name = "Centerline",
                ControlType = ControlType.Button,
                Description = "Add centerline annotation",
                Category = "Annotation"
            },

            ["equations"] = new SolidWorksUIElement
            {
                CommandName = "Equations",
                AutomationId = "Item 32906",  // ✅ DISCOVERED
                Name = "Equations",
                ControlType = ControlType.Button,
                Description = "Open equations dialog",
                Category = "Tools"
            },

            ["designtable"] = new SolidWorksUIElement
            {
                CommandName = "Design Table",
                AutomationId = "Item 37984",  // ✅ DISCOVERED
                Name = "Design Table",
                ControlType = ControlType.Button,
                Description = "Create or edit design table",
                Category = "Tools"
            }
        };

        /// <summary>
        /// Find an element by any name variant (command name, display name, or alternate names)
        /// </summary>
        public static SolidWorksUIElement? FindByName(string searchTerm)
        {
            if (string.IsNullOrWhiteSpace(searchTerm))
                return null;

            searchTerm = searchTerm.Trim().ToLower();

            // First try exact key match
            if (Elements.TryGetValue(searchTerm.Replace(" ", ""), out var exactMatch))
            {
                return exactMatch;
            }

            // Then search through all properties
            foreach (var kvp in Elements)
            {
                var element = kvp.Value;

                // Check command name
                if (element.CommandName.ToLower().Contains(searchTerm))
                    return element;

                // Check display name
                if (element.Name.ToLower().Contains(searchTerm))
                    return element;

                // Check alternate names
                if (element.AlternateNames?.Any(n => n.ToLower().Contains(searchTerm)) ?? false)
                    return element;

                // Check description
                if (element.Description.ToLower().Contains(searchTerm))
                    return element;
            }

            return null;
        }

        /// <summary>
        /// Get all elements in a specific category
        /// </summary>
        public static List<SolidWorksUIElement> GetByCategory(string category)
        {
            return Elements.Values
                .Where(e => e.Category.Equals(category, StringComparison.OrdinalIgnoreCase))
                .ToList();
        }

        /// <summary>
        /// Get all available categories
        /// </summary>
        public static List<string> GetCategories()
        {
            return Elements.Values
                .Select(e => e.Category)
                .Distinct()
                .OrderBy(c => c)
                .ToList();
        }

        /// <summary>
        /// Search for elements matching a query
        /// </summary>
        public static List<SolidWorksUIElement> Search(string query)
        {
            if (string.IsNullOrWhiteSpace(query))
                return Elements.Values.ToList();

            query = query.ToLower();

            return Elements.Values
                .Where(e =>
                    e.CommandName.ToLower().Contains(query) ||
                    e.Name.ToLower().Contains(query) ||
                    e.Description.ToLower().Contains(query) ||
                    (e.AlternateNames?.Any(n => n.ToLower().Contains(query)) ?? false))
                .ToList();
        }
    }
}

