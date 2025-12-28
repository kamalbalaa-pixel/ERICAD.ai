namespace Frontend.Models
{
    /// <summary>
    /// Represents the current connection state of the WebSocket.
    /// </summary>
    public enum ConnectionState
    {
        Disconnected,
        Connecting,
        Connected,
        Reconnecting,
        Error
    }
}









