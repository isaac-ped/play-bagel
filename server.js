const express = require('express')
const app = express()
var server = require('http').Server(app)
var io = require('socket.io')(server);
var fs = require('fs')
var valid_words = fs.readFileSync('full_dictionary.txt', 'utf-8').split('\n')
console.log(valid_words)

var is_word = function(word) {
    return valid_words.indexOf(word.toLowerCase()) > -1;
}

server.listen(8080);

app.get('/', function(req, res) {
    res.sendFile(__dirname + '/index.html');
});

var send_err = function(socket, msg) {
    socket.emit('err', { message : msg });
}

function Connection(socket, name, word, game) {
    this.game = game;
    this.name = name;
    this.word = word;
    this.socket = socket;
    this.last_emission = null;

    var emissions = [
        'joined',
        'started',
        'guess',
        'wait',
        'guessed',
        'responded',
        'lose',
        'win'
    ];

    for (var i = 0; i < emissions.length; i++) {
        let emission = '' + emissions[i].slice(0);
        this[emission] = function() {
            console.log(this.name, emission);
            this.socket.emit(emission, this.game.data());
            this.last_emission = emission;
        }
        console.log("registered", emission)
    }

}

function Game(name) {
    this.name = name;
    var started = false;
    this.players = {};
    this.active_player = null;
    this.waiting_player = null;
    this.active_guess = null;
    this.guesses = [];

    this.data = function() {
        return {
            name: this.name,
            players : Object.keys(this.players),
            active_guess : this.active_guess,
            guesses : this.guesses
        }
    };

    this.num_players = function() {
        return Object.keys(this.players).length;
    };

    this.swap_active = function() {
        var tmp = this.active_player;
        this.active_player = this.waiting_player;
        this.waiting_player = tmp;
    };

    this.start = function() {
        this.started = true;
        names = Object.keys(this.players);
        this.active_player = this.players[names[0]];
        this.waiting_player = this.players[names[1]];

        this.active_player.started();
        this.waiting_player.started();

        this.active_player.guess();
        this.waiting_player.wait();
    };

    this.is_active = function(name, socket) {
        if (!this.started) {
            return false;
        }
        if (this.active_player.name != name) {
            send_err(socket, "Not your turn!");
            return false;
        }
        return true;
    }

    this.guess = function(name, guess, socket) {
        if (!this.is_active(name, socket)) {
            return;
        }
        if (!is_word(guess)) {
            send_err(socket, "Please enter REAL word!");
            return;
        }
        this.active_guess = guess;
        this.swap_active();
        this.active_player.guessed();
        this.waiting_player.wait();
    };

    this.response = function(name, response, socket) {
        if (!this.is_active(name, socket)) {
            return;
        }
        var waiter = this.waiting_player.name;
        this.guesses.push(
            {player: waiter,
             guess: this.active_guess,
             resp: response
            });
        this.waiting_player.responded();
        this.active_player.guess();
    }

    this.correct = function(name, socket) {
        if (!this.is_active(name, socket)) {
            return;
        }
        var waiter = this.waiting_player.name;
        this.guesses.push(
            {player: waiter,
             guess: this.active_guess,
             resp: 5
            });
        this.waiting_player.win();
        this.active_player.lose();
    }

    this.join = function(name, word, socket) {
        if (name in this.players) {
            if (word != this.players[name].word) {
                send_err(socket, "Player already in game with different word!");
                return;
            }
            console.log('rejoining');
            var cnx = this.players[name];
            var last_emission = cnx.last_emission;
            cnx.socket = socket;
            cnx.joined();
            cnx[last_emission]();
        } else if (this.num_players() < 2) {
            console.log('joining');
            if (!is_word(word)) {
                send_err(socket, "Please enter a REAL word");
                return;
            }
            var cnx = new Connection(socket, name, word, this);
            this.players[name] = cnx;
            cnx.joined();

            if (this.num_players() == 2) {
                this.start();
            }
        } else {
            console.log('game full');
            send_err(socket, "Game full");
        }
    };

};

var games = {}

var get_game = function(name) {
    if (!(name in games)) {
        games[name] = new Game(name);
    }
    return games[name];
};

var del_game = function(name) {
    if (name in games) {
        delete games[name];
    }
};

io.on('connection', function(socket) {

    socket.emit('status', {message: 'connected'});

    socket.on('join', function(data) {
        console.log('joined', data);
        var game = get_game(data.game);
        game.join(data.player, data.word, socket);
    });

    socket.on('guess', function(data) {
        console.log('guess', data);
        var game = get_game(data.game);
        game.guess(data.player, data.guess, socket);
    });

    socket.on('response', function(data) {
        console.log('response', data);
        var game = get_game(data.game);
        game.response(data.player, data.response, socket);
    });

    socket.on('correct', function(data) {
        console.log('correct', data);
        var game = get_game(data.game);
        game.correct(data.player, socket);
        del_game(data.game);
    });

});
