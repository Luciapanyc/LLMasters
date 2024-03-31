$(document).ready(function () {
  $('#sendMessageBtn').click(function () {
      sendMessage();
  });

  $('#userMessage').keypress(function (e) {
      if (e.which === 13) { // Enter key pressed
          sendMessage();
      }
  });

  function sendMessage() {
      var userMessage = $('#userMessage').val().trim();
      if (userMessage.length === 0) return;

      var userMessageHtml =
          `<div class="chat message">
              <img src="../static/profile-2.jpg">
              <span>${userMessage}</span>
          </div>`;

      $('#messageBox').append(userMessageHtml);
      $('#userMessage').val(''); // Clear input field after sending message

      // Send message to Flask server
      $.ajax({
          type: 'POST',
          url: '/chatbot',
          data: { message: userMessage },
          success: function (response) {
              var botResponseHtml =
                  `<div class="chat response">
                      <img src="../static/chatbot.jpg">
                      <span>${response}</span>
                  </div>`;
              $('#messageBox').append(botResponseHtml);
          },
          error: function () {
              console.error('Error sending message');
          }
      });
  }
});
