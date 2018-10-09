const express = require('express')
const app = express()
var server = require('http').Server(app)
var io = require('socket.io')(server);

server.listen(3000);

app.get('/', function(req, res) {
    res.sendFile(__dirname + '/index.html');
});

var send_err = function(socket, msg) {
    socket.emit('err', { message : msg });
}

function Connection(socket, name, game) {
    this.game = game;
    this.name = name;
    this.socket = socket;

    this.joined = function(){
        console.log(this.name, 'joined');
        this.socket.emit('joined', this.game.data());
    };

    this.started = function() {
        this.socket.emit('started', this.game.data());
    };

    this.guess = function() {
        this.socket.emit('guess', this.game.data());
    }

    this.wait = function() {
        this.socket.emit('wait', this.game.data());
    }

    this.guessed = function() {
        this.socket.emit('guessed', this.game.data());
    }

    this.responded = function() {
        this.socket.emit('responded', this.game.data());
    }

    this.win = function() {
        this.socket.emit('win', this.game.data());
    }

    this.lose = function() {
        this.socket.emit('lose', this.game.data());
    }
}

function Game(name) {
    this.name = name;
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
        names = Object.keys(this.players);
        this.active_player = this.players[names[0]];
        this.waiting_player = this.players[names[1]];

        this.active_player.started();
        this.waiting_player.started();

        this.active_player.guess();
        this.waiting_player.wait();
    };

    this.is_active = function(name, socket) {
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

    this.join = function(name, socket) {
        if (name in this.players) {
            console.log('rejoining');
            var cnx = new Connection(socket, name, this);
            this.players[name] = cnx;
            cnx.joined();
        } else if (this.num_players() < 2) {
            console.log('joining');
            var cnx = new Connection(socket, name, this);
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
        game.join(data.player, socket);
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
