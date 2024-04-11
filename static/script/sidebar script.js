function redirectTo(page) {
    fetch(`/redirect_custom?page=${page}`, {
        method: 'GET'  // Specify GET method explicitly
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                console.log('Invalid page');
            }
        })
        .catch(error => {
            console.error('There was a problem with your fetch operation:', error);
        });
}
