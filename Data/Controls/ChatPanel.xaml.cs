using System;
using System.Collections.ObjectModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;
using Frontend.Models;

namespace Frontend.Controls
{
    /// <summary>
    /// Chat panel with message display and input.
    /// </summary>
    public partial class ChatPanel : UserControl
    {
        /// <summary>
        /// Event fired when the user wants to send a message.
        /// </summary>
        public event Action<string>? MessageSubmitted;

        public ChatPanel()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Sets the messages collection to display.
        /// </summary>
        public void SetMessagesSource(ObservableCollection<ChatMessage> messages)
        {
            ChatMessages.ItemsSource = messages;
        }

        /// <summary>
        /// Enables or disables the input controls.
        /// </summary>
        public void SetEnabled(bool enabled)
        {
            ChatInput.IsEnabled = enabled;
            SendButton.IsEnabled = enabled;
        }

        /// <summary>
        /// Scrolls the chat to the bottom.
        /// </summary>
        public void ScrollToBottom()
        {
            Dispatcher.BeginInvoke(DispatcherPriority.Loaded, new Action(() =>
            {
                ChatScrollViewer.ScrollToEnd();
            }));
        }

        /// <summary>
        /// Clears the input text.
        /// </summary>
        public void ClearInput()
        {
            ChatInput.Text = "";
        }

        /// <summary>
        /// Gets the current input text.
        /// </summary>
        public string GetInputText()
        {
            return ChatInput.Text?.Trim() ?? "";
        }

        private void ChatInput_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter && !Keyboard.Modifiers.HasFlag(ModifierKeys.Shift))
            {
                e.Handled = true;
                SubmitMessage();
            }
        }

        private void SendButton_Click(object sender, RoutedEventArgs e)
        {
            SubmitMessage();
        }

        private void SubmitMessage()
        {
            var message = GetInputText();
            if (!string.IsNullOrEmpty(message))
            {
                MessageSubmitted?.Invoke(message);
            }
        }
    }
}









