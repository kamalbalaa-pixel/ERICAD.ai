using System;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Frontend.Models;
using Frontend.Services;

namespace Frontend
{
    /// <summary>
    /// Main window for the ERICAD overlay application.
    /// Uses modular services and controls for each feature area.
    /// </summary>
    public partial class MainWindow : Window
    {
        // Services
        private readonly ChatService _chatService = new();
        private readonly WebSocketService _webSocketService = new();
        private readonly ScreenRecordingService _recordingService = new();
        private readonly ScreenCaptureService _captureService = new();
        private DrawingService? _drawingService;

        // Panel state
        private bool _isMinimized;
        private double _expandedWidth = 340;
        private double _expandedHeight;
        private bool _hasImageInSession;

        // Drag state
        private bool _isDragging;
        private Point _dragStartPoint;
        private double _panelStartRight;
        private double _panelStartTop;

        // Resize state
        private bool _isResizing;
        private Point _resizeStartPoint;
        private double _panelStartWidth;
        private double _panelStartHeight;

        public MainWindow()
        {
            InitializeComponent();
            InitializeServices();
            InitializeControls();
        }

        #region Initialization

        private void InitializeServices()
        {
            // Chat service
            _chatService.MessageAdded += () => ChatCtrl.ScrollToBottom();

            // WebSocket service
            _webSocketService.StateChanged += OnConnectionStateChanged;
            _webSocketService.MessageReceived += OnMessageReceived;
            _webSocketService.ErrorOccurred += msg => _chatService.AddErrorMessage(msg);
            _webSocketService.ConnectionLost += OnConnectionLost;

            // Recording service
            _recordingService.HasAnnotationsCheck = () => _drawingService?.HasUserDrawings ?? false;
            _recordingService.OnBeforeCapture = () => Dispatcher.Invoke(() => ControlPanel.Visibility = Visibility.Hidden);
            _recordingService.OnAfterCapture = () => Dispatcher.Invoke(() => ControlPanel.Visibility = Visibility.Visible);
            _recordingService.StatusUpdated += duration => Dispatcher.Invoke(() => CaptureCtrl.UpdateRecordingStatus(duration));

            // Capture service
            _captureService.OnBeforeCapture = () => Dispatcher.Invoke(() => ControlPanel.Visibility = Visibility.Hidden);
            _captureService.OnAfterCapture = () => Dispatcher.Invoke(() => ControlPanel.Visibility = Visibility.Visible);
        }

        private void InitializeControls()
        {
            // Set chat messages source
            ChatCtrl.SetMessagesSource(_chatService.Messages);

            // Header events
            Header.MinimizeToggled += OnMinimizeToggled;
            Header.CloseRequested += OnCloseRequested;
            Header.DragStarted += OnDragStarted;
            Header.DragMoved += OnDragMoved;
            Header.DragEnded += OnDragEnded;

            // Connection events
            ConnectionCtrl.ConnectionToggled += OnConnectionToggled;

            // Drawing events
            DrawingCtrl.DrawingModeToggled += OnDrawingModeToggled;
            DrawingCtrl.FadeModeToggled += enabled => { if (_drawingService != null) _drawingService.FadeEnabled = enabled; };
            DrawingCtrl.ClearRequested += () => _drawingService?.ClearAllDrawings();

            // Capture events
            CaptureCtrl.CaptureRequested += OnCaptureRequested;
            CaptureCtrl.NewChatRequested += OnNewChatRequested;

            // Chat events
            ChatCtrl.MessageSubmitted += OnChatMessageSubmitted;
        }

        private void Window_Loaded(object sender, RoutedEventArgs e)
        {
            // Initialize drawing service with the canvas
            _drawingService = new DrawingService(DrawingCanvas);
            _drawingService.DrawingModeChanged += OnDrawingModeChanged;
            _drawingService.StrokesCleared += () => DrawingCtrl.SetClearButtonVisible(_drawingService.IsDrawingMode);
            _drawingService.StrokeAdded += () => DrawingCtrl.SetClearButtonVisible(true);

            // Set panel dimensions
            ControlPanel.Width = 340;
            var maxPanelHeight = RootGrid.ActualHeight * 0.85;
            ControlPanel.MaxHeight = maxPanelHeight;
            _expandedHeight = Math.Min(RootGrid.ActualHeight - 80, maxPanelHeight);

            _chatService.AddSystemMessage("Welcome to ERICAD! Connect to the backend to get started.");
        }

        #endregion

        #region Connection Handling

        private async void OnConnectionToggled(bool connect)
        {
            if (connect)
            {
                _chatService.AddSystemMessage("Connecting to backend...");
                var success = await _webSocketService.ConnectAsync();

                if (success)
                {
                    _recordingService.Start();
                    CaptureCtrl.SetRecordingVisible(true);
                    _chatService.AddSystemMessage("✓ Connected! Recording started. Select time and capture.");
                }
            }
            else
            {
                _recordingService.Stop();
                CaptureCtrl.SetRecordingVisible(false);
                await _webSocketService.DisconnectAsync();
                _chatService.AddSystemMessage("Disconnected from backend.");
            }
        }

        private void OnConnectionStateChanged(ConnectionState state)
        {
            Dispatcher.Invoke(() =>
            {
                var isConnected = state == ConnectionState.Connected;
                ConnectionCtrl.SetConnected(isConnected);
                CaptureCtrl.SetEnabled(isConnected);
                ChatCtrl.SetEnabled(isConnected);

                if (!isConnected)
                {
                    _hasImageInSession = false;
                    CaptureCtrl.SetImageStatus(false, "");
                }
            });
        }

        private void OnConnectionLost()
        {
            Dispatcher.Invoke(() =>
            {
                _recordingService.Stop();
                CaptureCtrl.SetRecordingVisible(false);
                _chatService.AddSystemMessage("Server closed connection.");
            });
        }

        private void OnMessageReceived(string type, string content)
        {
            Dispatcher.Invoke(() =>
            {
                switch (type)
                {
                    case "image_received":
                        UpdateImageStatus(true, "📷 Image ready for questions");
                        _chatService.AddSystemMessage(content);
                        break;
                    case "video_received":
                        UpdateImageStatus(true, "🎬 Video ready for questions");
                        _chatService.AddSystemMessage(content);
                        break;
                    case "response":
                        _chatService.AddAIMessage(content);
                        break;
                    case "thinking":
                        _chatService.AddSystemMessage(content);
                        break;
                    case "session_cleared":
                        // Already handled in NewChatRequested
                        break;
                    case "error":
                        _chatService.AddErrorMessage(content);
                        break;
                    default:
                        _chatService.AddSystemMessage(content);
                        break;
                }
            });
        }

        #endregion

        #region Drawing

        private void DrawingCanvas_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            _drawingService?.OnMouseLeftButtonDown(e);
        }

        private void DrawingCanvas_MouseMove(object sender, MouseEventArgs e)
        {
            _drawingService?.OnMouseMove(e);
        }

        private void DrawingCanvas_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            _drawingService?.OnMouseLeftButtonUp(e);
        }

        private void OnDrawingModeToggled(bool enabled)
        {
            _drawingService?.SetDrawingMode(enabled);
        }

        private void OnDrawingModeChanged(bool isDrawingMode)
        {
            Header.SetMode(
                isDrawingMode ? "🎨 Drawing Mode" : "AI Assistant",
                isDrawingMode);
            DrawingCtrl.SetClearButtonVisible(isDrawingMode || (_drawingService?.HasUserDrawings ?? false));
        }

        private void Window_MouseRightButtonDown(object sender, MouseButtonEventArgs e)
        {
            // Right-click clears all drawings
            if (_drawingService?.HasUserDrawings == true)
            {
                _drawingService.ClearAllDrawings();
                e.Handled = true;
            }
        }

        #endregion

        #region Capture

        private async void OnCaptureRequested(int seconds)
        {
            if (!_webSocketService.IsConnected)
            {
                _chatService.AddErrorMessage("Not connected!");
                return;
            }

            try
            {
                CaptureCtrl.SetCaptureEnabled(false);

                if (seconds == 0)
                {
                    await CaptureScreenshot();
                }
                else
                {
                    await SendRecordedFrames(seconds);
                }
            }
            finally
            {
                CaptureCtrl.SetCaptureEnabled(true);
            }
        }

        private async Task CaptureScreenshot()
        {
            // Hide panel for capture
            ControlPanel.Visibility = Visibility.Hidden;
            await Task.Delay(100);

            try
            {
                var base64Image = await _captureService.CaptureScreenshotAsync();
                ControlPanel.Visibility = Visibility.Visible;

                await _webSocketService.SendImageAsync(base64Image, _drawingService?.HasUserDrawings ?? false);

                var annotationNote = _drawingService?.HasUserDrawings == true ? " with annotations" : "";
                _chatService.AddSystemMessage($"📷 Screenshot captured{annotationNote}. Ask me anything about it!");
            }
            catch (Exception ex)
            {
                ControlPanel.Visibility = Visibility.Visible;
                _chatService.AddErrorMessage($"Capture error: {ex.Message}");
            }
        }

        private async Task SendRecordedFrames(int seconds)
        {
            var frames = _recordingService.GetFramesForDuration(seconds);

            if (frames.Count == 0)
            {
                _chatService.AddErrorMessage("No frames recorded yet. Please wait a moment and try again.");
                return;
            }

            try
            {
                var payload = _captureService.PrepareFramesPayload(frames, seconds);

                await _webSocketService.SendFramesAsync(payload);

                var durationText = ScreenRecordingService.FormatDuration(seconds);
                var annotationNote = payload.HasAnnotations ? " (with annotations)" : "";
                _chatService.AddSystemMessage($"🎬 Sent last {durationText}{annotationNote}. Ask me anything!");
            }
            catch (Exception ex)
            {
                _chatService.AddErrorMessage($"Send error: {ex.Message}");
            }
        }

        private async void OnNewChatRequested()
        {
            if (!_webSocketService.IsConnected)
            {
                _chatService.AddErrorMessage("Not connected!");
                return;
            }

            try
            {
                await _webSocketService.SendNewSessionAsync();

                _chatService.Clear();
                _hasImageInSession = false;
                UpdateImageStatus(false, "");
                _recordingService.Reset();

                _chatService.AddSystemMessage("Session cleared. Capture a new screenshot to begin.");
            }
            catch (Exception ex)
            {
                _chatService.AddErrorMessage($"Error: {ex.Message}");
            }
        }

        private void UpdateImageStatus(bool hasImage, string statusText)
        {
            _hasImageInSession = hasImage;
            CaptureCtrl.SetImageStatus(hasImage, statusText);
        }

        #endregion

        #region Chat

        private async void OnChatMessageSubmitted(string message)
        {
            if (!_webSocketService.IsConnected)
            {
                _chatService.AddErrorMessage("Not connected to server!");
                return;
            }

            _chatService.AddUserMessage(message);
            ChatCtrl.ClearInput();

            try
            {
                await _webSocketService.SendChatAsync(message, ConnectionCtrl.GetSelectedModel());
            }
            catch (Exception ex)
            {
                _chatService.AddErrorMessage($"Send error: {ex.Message}");
            }
        }

        #endregion

        #region Panel Dragging

        private void OnDragStarted(Point startPoint)
        {
            _isDragging = true;
            _dragStartPoint = startPoint;
            _panelStartRight = Canvas.GetRight(ControlPanel);
            _panelStartTop = Canvas.GetTop(ControlPanel);

            if (double.IsNaN(_panelStartRight)) _panelStartRight = 20;
            if (double.IsNaN(_panelStartTop)) _panelStartTop = 40;
        }

        private void OnDragMoved(Point currentPoint)
        {
            if (!_isDragging) return;

            var deltaX = currentPoint.X - _dragStartPoint.X;
            var deltaY = currentPoint.Y - _dragStartPoint.Y;

            var newRight = _panelStartRight - deltaX;
            var newTop = _panelStartTop + deltaY;

            newRight = Math.Max(0, Math.Min(PanelCanvas.ActualWidth - ControlPanel.ActualWidth, newRight));
            newTop = Math.Max(0, Math.Min(PanelCanvas.ActualHeight - ControlPanel.ActualHeight, newTop));

            Canvas.SetRight(ControlPanel, newRight);
            Canvas.SetTop(ControlPanel, newTop);
        }

        private void OnDragEnded()
        {
            _isDragging = false;
        }

        #endregion

        #region Panel Resizing

        private void ResizeGrip_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (_isMinimized) return;

            _isResizing = true;
            _resizeStartPoint = e.GetPosition(PanelCanvas);
            _panelStartWidth = ControlPanel.ActualWidth;
            _panelStartHeight = ControlPanel.ActualHeight;

            ((UIElement)sender).CaptureMouse();
            e.Handled = true;
        }

        private void ResizeGrip_MouseMove(object sender, MouseEventArgs e)
        {
            if (!_isResizing) return;

            var currentPoint = e.GetPosition(PanelCanvas);
            var deltaX = currentPoint.X - _resizeStartPoint.X;
            var deltaY = currentPoint.Y - _resizeStartPoint.Y;

            var newWidth = _panelStartWidth - deltaX;
            var newHeight = _panelStartHeight + deltaY;

            // Constrain to reasonable bounds (max 85% of screen height)
            var maxHeight = Math.Min(PanelCanvas.ActualHeight * 0.85, PanelCanvas.ActualHeight - 40);
            newWidth = Math.Max(340, Math.Min(600, newWidth));
            newHeight = Math.Max(400, Math.Min(maxHeight, newHeight));

            ControlPanel.Width = newWidth;
            ControlPanel.Height = newHeight;
            _expandedWidth = newWidth;
            _expandedHeight = newHeight;
        }

        private void ResizeGrip_MouseLeftButtonUp(object sender, MouseButtonEventArgs e)
        {
            _isResizing = false;
            ((UIElement)sender).ReleaseMouseCapture();
        }

        #endregion

        #region Minimize/Expand

        private void OnMinimizeToggled(bool isMinimized)
        {
            _isMinimized = isMinimized;

            if (_isMinimized)
            {
                _expandedHeight = ControlPanel.ActualHeight;
                _expandedWidth = ControlPanel.ActualWidth;
                MainContent.Visibility = Visibility.Collapsed;
                ResizeGrip.Visibility = Visibility.Collapsed;
                ControlPanel.MinHeight = 0;
                ControlPanel.MaxHeight = double.PositiveInfinity;
                ControlPanel.Height = double.NaN;
            }
            else
            {
                MainContent.Visibility = Visibility.Visible;
                ResizeGrip.Visibility = Visibility.Visible;
                ControlPanel.MinHeight = 400;
                ControlPanel.MaxHeight = RootGrid.ActualHeight * 0.85;
                ControlPanel.Height = Math.Min(_expandedHeight, ControlPanel.MaxHeight);
            }

            Header.SetMinimizedState(_isMinimized);
        }

        #endregion

        #region Window Controls

        private async void OnCloseRequested()
        {
            await _webSocketService.DisconnectAsync();
            Application.Current.Shutdown();
        }

        #endregion
    }
}
