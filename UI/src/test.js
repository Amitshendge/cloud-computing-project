import axios from 'axios';

axios.get('https://x1px07x8w5.execute-api.us-east-1.amazonaws.com/development/presigned_upload?key=abc')
    .then(response => {
        console.log(response.data);
    })
    .catch(error => {
        console.error(error);
    });
