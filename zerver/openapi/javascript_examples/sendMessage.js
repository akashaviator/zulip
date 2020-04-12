const zulip = require('zulip-js');

// Pass the path to your zuliprc file here.
const config = {
    zuliprc: './.zuliprc',
};

// Send a stream message
zulip(config).then((client) => {
    // Send a message
    const params = {
        to: 'Denmark',
        type: 'stream',
        subject: 'Castle',
        content: 'I come not, friends, to steal away your hearts.'
    }

    client.messages.send(params).then(console.log);
});

// Send a private message
zulip(config).then((client) => {
    // Send a private message
    const user_id = 9;
    const params = {
        to: [user_id],
        type: 'private',
        content: 'With mirth and laughter let old wrinkles come.',
    }

    client.messages.send(params).then(console.log);
});
