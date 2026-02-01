using System.Windows;
using System.Windows.Media;

namespace Frontend.Models
{
    /// <summary>
    /// Represents a chat message in the conversation UI.
    /// </summary>
    public class ChatMessage
    {
        public string Text { get; set; } = "";
        public Brush Background { get; set; } = new SolidColorBrush(Color.FromRgb(51, 51, 51));
        public Brush Foreground { get; set; } = Brushes.White;
        public HorizontalAlignment Alignment { get; set; } = HorizontalAlignment.Left;
        public ChatMessageType Type { get; set; } = ChatMessageType.AI;
    }

    /// <summary>
    /// Type of chat message for styling purposes.
    /// </summary>
    public enum ChatMessageType
    {
        System,
        User,
        AI,
        Error
    }
}









