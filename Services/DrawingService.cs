using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;

namespace Frontend.Services
{
    /// <summary>
    /// Manages drawing/annotation functionality on the overlay canvas.
    /// </summary>
    public class DrawingService
    {
        private readonly Canvas _canvas;
        private readonly List<UIElement> _allStrokes = new();
        
        private bool _isDrawingMode;
        private bool _isDrawing;
        private bool _fadeEnabled;
        private Point _lastDrawPoint;
        private Polyline? _currentStroke;

        // Drawing configuration
        public double StrokeThickness { get; set; } = 3;
        public Color StrokeColor { get; set; } = Color.FromRgb(255, 80, 0); // Bright Orange
        public TimeSpan FadeDuration { get; set; } = TimeSpan.FromSeconds(3);

        /// <summary>
        /// Whether there are any user drawings on the canvas.
        /// </summary>
        public bool HasUserDrawings => _allStrokes.Count > 0;

        /// <summary>
        /// Whether drawing mode is currently enabled.
        /// </summary>
        public bool IsDrawingMode => _isDrawingMode;

        /// <summary>
        /// Whether fade mode is enabled for disappearing ink.
        /// </summary>
        public bool FadeEnabled
        {
            get => _fadeEnabled;
            set => _fadeEnabled = value;
        }

        /// <summary>
        /// Event fired when drawing mode changes.
        /// </summary>
        public event Action<bool>? DrawingModeChanged;

        /// <summary>
        /// Event fired when strokes are cleared.
        /// </summary>
        public event Action? StrokesCleared;

        /// <summary>
        /// Event fired when a stroke is added.
        /// </summary>
        public event Action? StrokeAdded;

        public DrawingService(Canvas canvas)
        {
            _canvas = canvas;
        }

        /// <summary>
        /// Toggles drawing mode on/off.
        /// </summary>
        public void ToggleDrawingMode()
        {
            SetDrawingMode(!_isDrawingMode);
        }

        /// <summary>
        /// Sets drawing mode to the specified state.
        /// </summary>
        public void SetDrawingMode(bool enabled)
        {
            _isDrawingMode = enabled;

            if (_isDrawingMode)
            {
                // Enable hit testing so canvas captures mouse events
                _canvas.IsHitTestVisible = true;
                _canvas.Background = new SolidColorBrush(Color.FromArgb(1, 0, 0, 0));
                _canvas.Cursor = Cursors.Pen;
            }
            else
            {
                // Disable hit testing so clicks pass through to desktop
                _canvas.IsHitTestVisible = false;
                _canvas.Background = Brushes.Transparent;
                _canvas.Cursor = Cursors.Arrow;
            }

            DrawingModeChanged?.Invoke(_isDrawingMode);
        }

        /// <summary>
        /// Handles mouse down to start a new stroke.
        /// </summary>
        public void OnMouseLeftButtonDown(MouseButtonEventArgs e)
        {
            if (!_isDrawingMode) return;

            _isDrawing = true;
            _lastDrawPoint = e.GetPosition(_canvas);

            // Start a new stroke
            _currentStroke = new Polyline
            {
                Stroke = new SolidColorBrush(StrokeColor),
                StrokeThickness = StrokeThickness,
                StrokeLineJoin = PenLineJoin.Round,
                StrokeStartLineCap = PenLineCap.Round,
                StrokeEndLineCap = PenLineCap.Round
            };
            _currentStroke.Points.Add(_lastDrawPoint);
            _canvas.Children.Add(_currentStroke);
            _allStrokes.Add(_currentStroke);

            _canvas.CaptureMouse();
            e.Handled = true;

            StrokeAdded?.Invoke();
        }

        /// <summary>
        /// Handles mouse move to continue the current stroke.
        /// </summary>
        public void OnMouseMove(MouseEventArgs e)
        {
            if (!_isDrawing || _currentStroke == null) return;

            var currentPoint = e.GetPosition(_canvas);
            _currentStroke.Points.Add(currentPoint);
            _lastDrawPoint = currentPoint;
        }

        /// <summary>
        /// Handles mouse up to finish the current stroke.
        /// </summary>
        public void OnMouseLeftButtonUp(MouseButtonEventArgs e)
        {
            if (!_isDrawing) return;

            _isDrawing = false;
            _canvas.ReleaseMouseCapture();

            // If fade is enabled, start fading animation
            if (_fadeEnabled && _currentStroke != null)
            {
                StartFadeAnimation(_currentStroke);
            }

            _currentStroke = null;
        }

        private void StartFadeAnimation(Polyline stroke)
        {
            var fadeAnimation = new DoubleAnimation
            {
                From = 1.0,
                To = 0.0,
                Duration = FadeDuration,
                EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn }
            };

            fadeAnimation.Completed += (s, e) =>
            {
                Application.Current.Dispatcher.Invoke(() =>
                {
                    _canvas.Children.Remove(stroke);
                    _allStrokes.Remove(stroke);

                    if (_allStrokes.Count == 0)
                    {
                        StrokesCleared?.Invoke();
                    }
                });
            };

            stroke.BeginAnimation(UIElement.OpacityProperty, fadeAnimation);
        }

        /// <summary>
        /// Clears all drawings from the canvas.
        /// </summary>
        public void ClearAllDrawings()
        {
            foreach (var stroke in _allStrokes.ToArray())
            {
                _canvas.Children.Remove(stroke);
            }
            _allStrokes.Clear();
            StrokesCleared?.Invoke();
        }
    }
}









