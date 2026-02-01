using System;
using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Media;
using Frontend.Models;

namespace Frontend.Services
{
    /// <summary>
    /// Manages chat messages and conversation state.
    /// </summary>
    public class ChatService
    {
        private static readonly Color AccentColor = Color.FromRgb(255, 107, 53);
        private static readonly Color SystemBgColor = Color.FromRgb(40, 40, 40);
        private static readonly Color SystemFgColor = Color.FromRgb(150, 150, 150);
        private static readonly Color AIBgColor = Color.FromRgb(45, 45, 45);
        private static readonly Color ErrorBgColor = Color.FromRgb(80, 30, 30);
        private static readonly Color ErrorFgColor = Color.FromRgb(255, 150, 150);

        public ObservableCollection<ChatMessage> Messages { get; } = new();

        /// <summary>
        /// Event fired when a new message is added.
        /// </summary>
        public event Action? MessageAdded;

        public void AddSystemMessage(string message)
        {
            Messages.Add(new ChatMessage
            {
                Text = message,
                Background = new SolidColorBrush(SystemBgColor),
                Foreground = new SolidColorBrush(SystemFgColor),
                Alignment = HorizontalAlignment.Center,
                Type = ChatMessageType.System
            });
            MessageAdded?.Invoke();
        }

        public void AddUserMessage(string message)
        {
            Messages.Add(new ChatMessage
            {
                Text = message,
                Background = new SolidColorBrush(AccentColor),
                Foreground = Brushes.White,
                Alignment = HorizontalAlignment.Right,
                Type = ChatMessageType.User
            });
            MessageAdded?.Invoke();
        }

        public void AddAIMessage(string message)
        {
            Messages.Add(new ChatMessage
            {
                Text = message,
                Background = new SolidColorBrush(AIBgColor),
                Foreground = Brushes.White,
                Alignment = HorizontalAlignment.Left,
                Type = ChatMessageType.AI
            });
            MessageAdded?.Invoke();
        }

        public void AddErrorMessage(string message)
        {
            Messages.Add(new ChatMessage
            {
                Text = message,
                Background = new SolidColorBrush(ErrorBgColor),
                Foreground = new SolidColorBrush(ErrorFgColor),
                Alignment = HorizontalAlignment.Center,
                Type = ChatMessageType.Error
            });
            MessageAdded?.Invoke();
        }

        public void Clear()
        {
            Messages.Clear();
        }
    }
}









