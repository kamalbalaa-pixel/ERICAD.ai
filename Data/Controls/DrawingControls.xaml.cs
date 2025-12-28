using System;
using System.Windows;
using System.Windows.Controls;

namespace Frontend.Controls
{
    /// <summary>
    /// Controls for drawing/annotation mode.
    /// </summary>
    public partial class DrawingControls : UserControl
    {
        /// <summary>
        /// Event fired when drawing mode is toggled.
        /// </summary>
        public event Action<bool>? DrawingModeToggled;

        /// <summary>
        /// Event fired when fade mode is toggled.
        /// </summary>
        public event Action<bool>? FadeModeToggled;

        /// <summary>
        /// Event fired when clear drawing is clicked.
        /// </summary>
        public event Action? ClearRequested;

        public DrawingControls()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Shows or hides the clear button.
        /// </summary>
        public void SetClearButtonVisible(bool visible)
        {
            ClearDrawingButton.Visibility = visible ? Visibility.Visible : Visibility.Collapsed;
        }

        /// <summary>
        /// Updates the drawing mode toggle state.
        /// </summary>
        public void SetDrawingMode(bool isEnabled)
        {
            DrawToggle.IsChecked = isEnabled;
        }

        private void DrawToggle_Click(object sender, RoutedEventArgs e)
        {
            DrawingModeToggled?.Invoke(DrawToggle.IsChecked == true);
        }

        private void FadeToggle_Click(object sender, RoutedEventArgs e)
        {
            FadeModeToggled?.Invoke(FadeToggle.IsChecked == true);
        }

        private void ClearDrawingButton_Click(object sender, RoutedEventArgs e)
        {
            ClearRequested?.Invoke();
        }
    }
}









