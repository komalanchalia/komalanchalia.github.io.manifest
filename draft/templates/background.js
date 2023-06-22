document.getElementById('summarizeForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const choice = document.getElementById('toggleSwitch').checked ? 'Text-Rank' : 'LSA';
  
    // Function to get the URL of the current YouTube tab
    function getCurrentTabUrl(callback) {
      chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        const tab = tabs[0];
        const url = tab.url;
        callback(url);
      });
    }
  
    // Call the function to get the current tab URL
    getCurrentTabUrl(function(url) {
      if (url) {
        fetch(`http://localhost:5000/transcript-fetch?current_tab_url=${encodeURIComponent(url)}&choice=${encodeURIComponent(choice)}`)
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              document.getElementById('summary').textContent = data.response;
              document.getElementById('resultContainer').style.display = 'block';
            } else {
              alert(data.message);
            }
          })
          .catch(error => {
            console.error('An error occurred:', error);
            alert('An error occurred. Please try again later.');
          });
      } else {
        console.error('Unable to retrieve tab URL');
        alert('An error occurred. Please try again later.');
      }
    });
  });
  