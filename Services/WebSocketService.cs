using System;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Frontend.Models;

namespace Frontend.Services
{
    /// <summary>
    /// Manages WebSocket connection to the backend server.
    /// </summary>
    public class WebSocketService : IDisposable
    {
        private ClientWebSocket? _client;
        private CancellationTokenSource? _receiveCts;
        
        // Use camelCase for JSON serialization to match Python backend expectations
        private static readonly JsonSerializerOptions _jsonOptions = new()
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };

        public string ServerUri { get; set; } = "ws://127.0.0.1:8000/ws";
        public TimeSpan ConnectionTimeout { get; set; } = TimeSpan.FromSeconds(2);

        /// <summary>
        /// Current connection state.
        /// </summary>
        public ConnectionState State { get; private set; } = ConnectionState.Disconnected;

        /// <summary>
        /// Whether the connection is open and ready.
        /// </summary>
        public bool IsConnected => _client?.State == WebSocketState.Open;

        /// <summary>
        /// Event fired when connection state changes.
        /// </summary>
        public event Action<ConnectionState>? StateChanged;

        /// <summary>
        /// Event fired when a message is received from the server.
        /// </summary>
        public event Action<string, string>? MessageReceived;

        /// <summary>
        /// Event fired when an error occurs.
        /// </summary>
        public event Action<string>? ErrorOccurred;

        /// <summary>
        /// Event fired when connection is lost.
        /// </summary>
        public event Action? ConnectionLost;

        public async Task<bool> ConnectAsync()
        {
            try
            {
                SetState(ConnectionState.Connecting);

                _client = new ClientWebSocket();
                _receiveCts = new CancellationTokenSource();

                using var cts = new CancellationTokenSource(ConnectionTimeout);
                await _client.ConnectAsync(new Uri(ServerUri), cts.Token);

                SetState(ConnectionState.Connected);

                // Start receive loop
                _ = ReceiveLoopAsync(_receiveCts.Token);

                return true;
            }
            catch (OperationCanceledException)
            {
                ErrorOccurred?.Invoke("Connection timed out. Is the backend running?");
                Cleanup();
                SetState(ConnectionState.Disconnected);
                return false;
            }
            catch (Exception ex)
            {
                ErrorOccurred?.Invoke($"Connection error: {ex.Message}");
                Cleanup();
                SetState(ConnectionState.Error);
                return false;
            }
        }

        public async Task DisconnectAsync()
        {
            if (_client == null) return;

            try
            {
                _receiveCts?.Cancel();

                if (_client.State == WebSocketState.Open)
                {
                    await _client.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Disconnect error: {ex.Message}");
            }
            finally
            {
                Cleanup();
                SetState(ConnectionState.Disconnected);
            }
        }

        public async Task SendAsync(object data)
        {
            if (_client?.State != WebSocketState.Open)
            {
                throw new InvalidOperationException("Not connected to server");
            }

            var jsonMessage = JsonSerializer.Serialize(data, _jsonOptions);
            System.Diagnostics.Debug.WriteLine($"[WebSocket] Sending: {jsonMessage.Substring(0, Math.Min(200, jsonMessage.Length))}...");
            var bytes = Encoding.UTF8.GetBytes(jsonMessage);
            await _client.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
        }

        public async Task SendChatAsync(string message, string model)
        {
            await SendAsync(new { type = "chat", message, model });
        }

        public async Task SendImageAsync(string base64Image, bool hasAnnotations)
        {
            await SendAsync(new { type = "image", data = base64Image, hasAnnotations });
        }

        public async Task SendFramesAsync(object framesData)
        {
            await SendAsync(framesData);
        }

        public async Task SendNewSessionAsync()
        {
            await SendAsync(new { type = "new_session" });
        }

        private async Task ReceiveLoopAsync(CancellationToken cancellationToken)
        {
            var buffer = new byte[32768]; // Larger buffer for AI responses

            try
            {
                while (_client?.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
                {
                    var messageBuilder = new StringBuilder();
                    WebSocketReceiveResult result;

                    do
                    {
                        result = await _client.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken);
                        messageBuilder.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
                    } while (!result.EndOfMessage);

                    if (result.MessageType == WebSocketMessageType.Text)
                    {
                        ProcessMessage(messageBuilder.ToString());
                    }
                    else if (result.MessageType == WebSocketMessageType.Close)
                    {
                        ConnectionLost?.Invoke();
                        break;
                    }
                }
            }
            catch (OperationCanceledException)
            {
                // Normal cancellation, ignore
            }
            catch (Exception ex)
            {
                ErrorOccurred?.Invoke($"Connection lost: {ex.Message}");
                ConnectionLost?.Invoke();
            }
            finally
            {
                SetState(ConnectionState.Disconnected);
            }
        }

        private void ProcessMessage(string message)
        {
            try
            {
                var json = JsonDocument.Parse(message);
                var msgType = json.RootElement.GetProperty("type").GetString() ?? "";
                var msgContent = json.RootElement.GetProperty("message").GetString() ?? "";

                MessageReceived?.Invoke(msgType, msgContent);
            }
            catch (JsonException)
            {
                // Legacy plain text message
                MessageReceived?.Invoke("response", message);
            }
        }

        private void SetState(ConnectionState state)
        {
            if (State != state)
            {
                State = state;
                StateChanged?.Invoke(state);
            }
        }

        private void Cleanup()
        {
            _receiveCts?.Cancel();
            _receiveCts?.Dispose();
            _receiveCts = null;

            _client?.Dispose();
            _client = null;
        }

        public void Dispose()
        {
            Cleanup();
        }
    }
}




