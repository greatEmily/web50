document.addEventListener('DOMContentLoaded', function() {

  // Button clicks
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', compose_email);

  // Form submission (Spec 1)
  document.querySelector('#compose-form').onsubmit = function(event) {
    event.preventDefault();

    const recipients = document.querySelector('#compose-recipients').value;
    const subject = document.querySelector('#compose-subject').value;
    const body = document.querySelector('#compose-body').value;

    fetch('/emails', {
      method: 'POST',
      body: JSON.stringify({
        recipients: recipients,
        subject: subject,
        body: body
      })
    })
    .then(response => response.json())
    .then(result => {
      console.log(result);
      load_mailbox('sent');
    });
  };

  // Load inbox by default
  load_mailbox('inbox');
});


function compose_email() {

  // Show compose view and hide others
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#email-detail-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  // Clear fields
  document.querySelector('#compose-recipients').value = '';
  document.querySelector('#compose-subject').value = '';
  document.querySelector('#compose-body').value = '';
}


function load_email(id) {

  // Show the detail view, hide others
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'none';
  document.querySelector('#email-detail-view').style.display = 'block';

  // Fetch the email
  fetch(`/emails/${id}`)
    .then(response => response.json())
    .then(email => {

      // Mark as read
      if (!email.read) {
        fetch(`/emails/${id}`, {
          method: 'PUT',
          body: JSON.stringify({ read: true })
        });
      }

      // Build the detail view
      const detail = document.querySelector('#email-detail-view');
      detail.innerHTML = `
        <h4>${email.subject}</h4>
        <p><strong>From:</strong> ${email.sender}</p>
        <p><strong>To:</strong> ${email.recipients.join(', ')}</p>
        <p><strong>Timestamp:</strong> ${email.timestamp}</p>

        <button id="reply-btn" class="btn btn-sm btn-outline-primary">Reply</button>
        ${email.sender !== CURRENT_USER ? 
          `<button id="archive-btn" class="btn btn-sm btn-outline-secondary">
            ${email.archived ? "Unarchive" : "Archive"}
          </button>` 
        : ""}

        <hr>
        <p>${email.body.replace(/\n/g, '<br>')}</p>
      `;

      // Archive / Unarchive button
      if (email.sender !== CURRENT_USER) {
        const archiveBtn = document.querySelector('#archive-btn');
        archiveBtn.addEventListener('click', () => {

          fetch(`/emails/${id}`, {
            method: 'PUT',
            body: JSON.stringify({
              archived: !email.archived
            })
          })
          .then(() => load_mailbox('inbox'));
        });
      }

      // Reply button
      document.querySelector('#reply-btn').addEventListener('click', () => {
        compose_email();

        // Pre-fill recipients
        document.querySelector('#compose-recipients').value = email.sender;

        // Pre-fill subject
        let subject = email.subject;
        if (!subject.startsWith("Re:")) {
          subject = "Re: " + subject;
        }
        document.querySelector('#compose-subject').value = subject;

        // Pre-fill body
        const quoted = `\n\nOn ${email.timestamp}, ${email.sender} wrote:\n${email.body}`;
        document.querySelector('#compose-body').value = quoted;
      });

    });
}


function load_mailbox(mailbox) {

  // Show mailbox view, hide others
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';
  document.querySelector('#email-detail-view').style.display = 'none';

  // Mailbox title
  document.querySelector('#emails-view').innerHTML =
    `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

  // Fetch mailbox contents (Spec 2)
  fetch(`/emails/${mailbox}`)
    .then(response => response.json())
    .then(emails => {

      emails.forEach(email => {

        // Email preview container
        const emailDiv = document.createElement('div');
        emailDiv.className = 'email-item';
        emailDiv.style.border = '1px solid #ccc';
        emailDiv.style.padding = '10px';
        emailDiv.style.margin = '5px';
        emailDiv.style.cursor = 'pointer';
        emailDiv.style.backgroundColor = email.read ? '#e6e6e6' : 'white';

        // Preview content
        emailDiv.innerHTML = `
          <strong>${mailbox === 'sent' ? email.recipients.join(', ') : email.sender}</strong>
          &nbsp;&nbsp; ${email.subject}
          <span style="float:right;">${email.timestamp}</span>
        `;

        // Click to open (Spec 3)
        emailDiv.addEventListener('click', () => load_email(email.id));

        document.querySelector('#emails-view').append(emailDiv);
      });
    });
}
