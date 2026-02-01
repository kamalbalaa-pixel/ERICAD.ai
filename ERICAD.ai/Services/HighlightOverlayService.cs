using System;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;
using System.Windows.Threading;

namespace Frontend.Services
{
    /// <summary>
    /// Service for creating highlight overlays on top of other windows
    /// </summary>
    public class HighlightOverlayService
    {
        private HighlightOverlayWindow? _overlayWindow;
        private DispatcherTimer? _pulseTimer;
        private bool _isPulsing;

        #region Win32 Imports for Click-Through Window

        [DllImport("user32.dll")]
        private static extern int SetWindowLong(IntPtr hwnd, int index, int newStyle);

        [DllImport("user32.dll")]
        private static extern int GetWindowLong(IntPtr hwnd, int index);

        private const int GWL_EXSTYLE = -20;
        private const int WS_EX_TRANSPARENT = 0x00000020;
        private const int WS_EX_LAYERED = 0x00080000;
        private const int WS_EX_TOOLWINDOW = 0x00000080;

        #endregion

        /// <summary>
        /// Shows the overlay window
        /// </summary>
        public void Show()
        {
            if (_overlayWindow == null)
            {
                _overlayWindow = new HighlightOverlayWindow();
                _overlayWindow.Show();
                MakeClickThrough(_overlayWindow);
            }
            else
            {
                _overlayWindow.Show();
            }
        }

        /// <summary>
        /// Hides the overlay window
        /// </summary>
        public void Hide()
        {
            _overlayWindow?.Hide();
            StopPulse();
        }

        /// <summary>
        /// Closes and disposes the overlay window
        /// </summary>
        public void Close()
        {
            StopPulse();
            _overlayWindow?.Close();
            _overlayWindow = null;
        }

        /// <summary>
        /// Highlights a rectangular region on screen with animation
        /// </summary>
        public void HighlightRegion(Rect region, string? label = null)
        {
            Show();
            _overlayWindow?.DrawHighlight(region, label);
            StartPulse();
        }

        /// <summary>
        /// Highlights a region with an arrow pointing to it
        /// </summary>
        public void HighlightWithArrow(Rect region, string? label = null, ArrowDirection arrowFrom = ArrowDirection.Left)
        {
            Show();
            _overlayWindow?.DrawHighlightWithArrow(region, label, arrowFrom);
            StartPulse();
        }

        /// <summary>
        /// Clears all highlights
        /// </summary>
        public void ClearHighlights()
        {
            StopPulse();
            _overlayWindow?.ClearAll();
        }

        private void MakeClickThrough(Window window)
        {
            var hwnd = new WindowInteropHelper(window).Handle;
            int extendedStyle = GetWindowLong(hwnd, GWL_EXSTYLE);
            SetWindowLong(hwnd, GWL_EXSTYLE, extendedStyle | WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_TOOLWINDOW);
        }

        private void StartPulse()
        {
            if (_isPulsing) return;
            _isPulsing = true;

            _pulseTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(500)
            };
            _pulseTimer.Tick += (s, e) => _overlayWindow?.Pulse();
            _pulseTimer.Start();
        }

        private void StopPulse()
        {
            _isPulsing = false;
            _pulseTimer?.Stop();
            _pulseTimer = null;
        }
    }

    /// <summary>
    /// Direction for arrow annotation
    /// </summary>
    public enum ArrowDirection
    {
        Left,
        Right,
        Top,
        Bottom
    }

    /// <summary>
    /// The actual overlay window that displays highlights
    /// </summary>
    internal class HighlightOverlayWindow : Window
    {
        private Canvas _canvas;
        private Rectangle? _highlightRect;
        private Polygon? _arrow;
        private TextBlock? _label;
        private Border? _labelBorder;
        private bool _pulseState;

        // Highlight colors
        private static readonly Color HighlightColor = Color.FromRgb(255, 200, 0); // Bright yellow
        private static readonly Color HighlightFillColor = Color.FromArgb(40, 255, 200, 0);
        private static readonly Color ArrowColor = Color.FromRgb(255, 107, 53); // ERICAD orange

        public HighlightOverlayWindow()
        {
            // Window setup for transparent overlay
            WindowStyle = WindowStyle.None;
            AllowsTransparency = true;
            Background = Brushes.Transparent;
            Topmost = true;
            ShowInTaskbar = false;
            ResizeMode = ResizeMode.NoResize;

            // Cover entire virtual screen (all monitors)
            Left = SystemParameters.VirtualScreenLeft;
            Top = SystemParameters.VirtualScreenTop;
            Width = SystemParameters.VirtualScreenWidth;
            Height = SystemParameters.VirtualScreenHeight;

            // Create canvas for drawing
            _canvas = new Canvas
            {
                Background = Brushes.Transparent
            };
            Content = _canvas;
        }

        public void DrawHighlight(Rect region, string? label)
        {
            ClearAll();

            // Adjust for virtual screen offset
            double offsetX = -SystemParameters.VirtualScreenLeft;
            double offsetY = -SystemParameters.VirtualScreenTop;

            // Create pulsing border rectangle
            _highlightRect = new Rectangle
            {
                Width = region.Width + 12,
                Height = region.Height + 12,
                Stroke = new SolidColorBrush(HighlightColor),
                StrokeThickness = 3,
                Fill = new SolidColorBrush(HighlightFillColor),
                RadiusX = 6,
                RadiusY = 6,
                Effect = new System.Windows.Media.Effects.DropShadowEffect
                {
                    Color = HighlightColor,
                    BlurRadius = 15,
                    ShadowDepth = 0,
                    Opacity = 0.8
                }
            };

            Canvas.SetLeft(_highlightRect, region.X - 6 + offsetX);
            Canvas.SetTop(_highlightRect, region.Y - 6 + offsetY);
            _canvas.Children.Add(_highlightRect);

            // Add label if provided
            if (!string.IsNullOrEmpty(label))
            {
                AddLabel(region, label, offsetX, offsetY);
            }
        }

        public void DrawHighlightWithArrow(Rect region, string? label, ArrowDirection arrowFrom)
        {
            DrawHighlight(region, label);

            double offsetX = -SystemParameters.VirtualScreenLeft;
            double offsetY = -SystemParameters.VirtualScreenTop;

            // Draw arrow pointing to the highlighted region
            DrawArrow(region, arrowFrom, offsetX, offsetY);
        }

        private void AddLabel(Rect region, string label, double offsetX, double offsetY)
        {
            _label = new TextBlock
            {
                Text = label,
                Foreground = Brushes.White,
                FontSize = 14,
                FontWeight = FontWeights.SemiBold,
                FontFamily = new FontFamily("Segoe UI")
            };

            _labelBorder = new Border
            {
                Background = new SolidColorBrush(Color.FromArgb(230, 30, 30, 30)),
                CornerRadius = new CornerRadius(4),
                Padding = new Thickness(10, 6, 10, 6),
                BorderBrush = new SolidColorBrush(ArrowColor),
                BorderThickness = new Thickness(2),
                Child = _label,
                Effect = new System.Windows.Media.Effects.DropShadowEffect
                {
                    Color = Colors.Black,
                    BlurRadius = 10,
                    ShadowDepth = 2,
                    Opacity = 0.5
                }
            };

            // Position label below the highlight
            Canvas.SetLeft(_labelBorder, region.X + offsetX);
            Canvas.SetTop(_labelBorder, region.Y + region.Height + 15 + offsetY);
            _canvas.Children.Add(_labelBorder);
        }

        private void DrawArrow(Rect targetRegion, ArrowDirection direction, double offsetX, double offsetY)
        {
            double arrowLength = 60;
            double arrowWidth = 16;
            Point start, end;

            switch (direction)
            {
                case ArrowDirection.Left:
                    start = new Point(targetRegion.X - arrowLength - 10 + offsetX, targetRegion.Y + targetRegion.Height / 2 + offsetY);
                    end = new Point(targetRegion.X - 10 + offsetX, targetRegion.Y + targetRegion.Height / 2 + offsetY);
                    break;
                case ArrowDirection.Right:
                    start = new Point(targetRegion.Right + arrowLength + 10 + offsetX, targetRegion.Y + targetRegion.Height / 2 + offsetY);
                    end = new Point(targetRegion.Right + 10 + offsetX, targetRegion.Y + targetRegion.Height / 2 + offsetY);
                    break;
                case ArrowDirection.Top:
                    start = new Point(targetRegion.X + targetRegion.Width / 2 + offsetX, targetRegion.Y - arrowLength - 10 + offsetY);
                    end = new Point(targetRegion.X + targetRegion.Width / 2 + offsetX, targetRegion.Y - 10 + offsetY);
                    break;
                case ArrowDirection.Bottom:
                default:
                    start = new Point(targetRegion.X + targetRegion.Width / 2 + offsetX, targetRegion.Bottom + arrowLength + 10 + offsetY);
                    end = new Point(targetRegion.X + targetRegion.Width / 2 + offsetX, targetRegion.Bottom + 10 + offsetY);
                    break;
            }

            // Arrow shaft
            var line = new Line
            {
                X1 = start.X,
                Y1 = start.Y,
                X2 = end.X,
                Y2 = end.Y,
                Stroke = new SolidColorBrush(ArrowColor),
                StrokeThickness = 4,
                StrokeStartLineCap = PenLineCap.Round
            };
            _canvas.Children.Add(line);

            // Arrow head
            _arrow = CreateArrowHead(end, start, arrowWidth, ArrowColor);
            _canvas.Children.Add(_arrow);

            // Animate the arrow
            AnimateArrow(line, direction);
        }

        private Polygon CreateArrowHead(Point tip, Point origin, double size, Color color)
        {
            double angle = Math.Atan2(tip.Y - origin.Y, tip.X - origin.X);
            double headAngle = Math.PI / 6; // 30 degrees

            Point left = new Point(
                tip.X - size * Math.Cos(angle - headAngle),
                tip.Y - size * Math.Sin(angle - headAngle)
            );

            Point right = new Point(
                tip.X - size * Math.Cos(angle + headAngle),
                tip.Y - size * Math.Sin(angle + headAngle)
            );

            return new Polygon
            {
                Points = new PointCollection { tip, left, right },
                Fill = new SolidColorBrush(color),
                Stroke = new SolidColorBrush(color),
                StrokeThickness = 1
            };
        }

        private void AnimateArrow(Line line, ArrowDirection direction)
        {
            DoubleAnimation animation;
            double offset = 15;

            switch (direction)
            {
                case ArrowDirection.Left:
                case ArrowDirection.Right:
                    animation = new DoubleAnimation
                    {
                        From = line.X1,
                        To = line.X1 + (direction == ArrowDirection.Left ? offset : -offset),
                        Duration = TimeSpan.FromMilliseconds(600),
                        AutoReverse = true,
                        RepeatBehavior = RepeatBehavior.Forever,
                        EasingFunction = new SineEase { EasingMode = EasingMode.EaseInOut }
                    };
                    line.BeginAnimation(Line.X1Property, animation);
                    break;
                case ArrowDirection.Top:
                case ArrowDirection.Bottom:
                    animation = new DoubleAnimation
                    {
                        From = line.Y1,
                        To = line.Y1 + (direction == ArrowDirection.Top ? offset : -offset),
                        Duration = TimeSpan.FromMilliseconds(600),
                        AutoReverse = true,
                        RepeatBehavior = RepeatBehavior.Forever,
                        EasingFunction = new SineEase { EasingMode = EasingMode.EaseInOut }
                    };
                    line.BeginAnimation(Line.Y1Property, animation);
                    break;
            }
        }

        public void Pulse()
        {
            if (_highlightRect == null) return;

            _pulseState = !_pulseState;

            double targetOpacity = _pulseState ? 0.6 : 1.0;
            double targetThickness = _pulseState ? 2.5 : 3.5;

            var opacityAnim = new DoubleAnimation
            {
                To = targetOpacity,
                Duration = TimeSpan.FromMilliseconds(400),
                EasingFunction = new SineEase { EasingMode = EasingMode.EaseInOut }
            };

            _highlightRect.BeginAnimation(OpacityProperty, opacityAnim);
            _highlightRect.StrokeThickness = targetThickness;
        }

        public void ClearAll()
        {
            _canvas.Children.Clear();
            _highlightRect = null;
            _arrow = null;
            _label = null;
            _labelBorder = null;
        }
    }
}

