using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace Frontend.Controls
{
    /// <summary>
    /// Header control with drag handle, mode indicator, and window controls.
    /// </summary>
    public partial class HeaderControl : UserControl
    {
        private bool _isDragging;
        private Point _dragStartPoint;
        private Window? _parentWindow;

        /// <summary>
        /// Event fired when the panel should be minimized/expanded.
        /// </summary>
        public event Action<bool>? MinimizeToggled;

        /// <summary>
        /// Event fired when the close button is clicked.
        /// </summary>
        public event Action? CloseRequested;

        /// <summary>
        /// Event fired when dragging starts.
        /// </summary>
        public event Action<Point>? DragStarted;

        /// <summary>
        /// Event fired during dragging.
        /// </summary>
        public event Action<Point>? DragMoved;

        /// <summary>
        /// Event fired when dragging ends.
        /// </summary>
        public event Action? DragEnded;

        public HeaderControl()
        {
            InitializeComponent();
            Loaded += (s, e) => _parentWindow = Window.GetWindow(this);
        }

        /// <summary>
        /// Sets the mode indicator text and color.
        /// </summary>
        public void SetMode(string mode, bool isDrawingMode = false)
        {
            ModeIndicator.Text = mode;
            ModeIndicator.Foreground = isDrawingMode 
                ? new SolidColorBrush(Color.FromRgb(255, 80, 0))
                : new SolidColorBrush(Color.FromRgb(102, 102, 102));
        }

        /// <summary>
        /// Sets the minimized state UI.
        /// </summary>
        public void SetMinimizedState(bool isMinimized)
        {
            MinimizeToggle.Content = isMinimized ? "▢" : "—";
            MinimizeToggle.ToolTip = isMinimized ? "Expand Panel" : "Minimize Panel";
        }

        private void DragHandle_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            _isDragging = true;
            // Get position relative to the parent window (fixed reference, WPF coordinates)
            _dragStartPoint = e.GetPosition(_parentWindow);
            DragStarted?.Invoke(_dragStartPoint);
            
            // Capture mouse and force cursor to stay as SizeAll
            Mouse.OverrideCursor = Cursors.SizeAll;
            ((UIElement)sender).CaptureMouse();
            e.Handled = true;
        }

        private void DragHandle_MouseMove(object sender, MouseEventArgs e)
        {
            if (!_isDragging || _parentWindow == null) return;
            
            // Get position relative to parent window (stable WPF coordinates)
            var currentPoint = e.GetPosition(_parentWindow);
            DragMoved?.Invoke(currentPoint);
            e.Handled = true;
        }

        private void DragHandle_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            if (_isDragging)
            {
                _isDragging = false;
                Mouse.OverrideCursor = null;
                ((UIElement)sender).ReleaseMouseCapture();
                DragEnded?.Invoke();
                e.Handled = true;
            }
        }

        private void MinimizeToggle_Click(object sender, RoutedEventArgs e)
        {
            var isMinimized = MinimizeToggle.IsChecked == true;
            MinimizeToggled?.Invoke(isMinimized);
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            CloseRequested?.Invoke();
        }
    }
}
