# Hearts

## Setup

### Requirements:
- Docker
- Docker Compose

### Building Image:
Run this to build the docker image
```bash
docker-compose build
```

### Running the Server with All Dependencies:
```bash
docker-compose up
```

### Running Django Manage Commands:
```
docker-compose run web python manage.py <command>
```
For example:
```bash
docker-compose run web python manage.py migrate
docker-compose run web python manage.py makemigrations
docker-compose run web python manage.py test
docker-compose run web python manage.py shell_plus
```

## Planning

**Features**
- Real-time multiplayer
  - Hosting vs joining games
  - Persistent games with server browser
- Bots
  - Bot can take over mid-game
  - Take over a bot if joining mid-game
- Basic UI
  - Function over form

**Components**
- Data
  - Tables:
    - Player
    - Match
    - Game
    - Trick
    - Card
    - PlayerCard
- API
  - Basic set of endpoints:
    - Get server list
    - Start game
    - Join game
    - Leave game
    - Play card
    - Send chat
  - Polling:
    - Get game state
- Front end
  - Landing page (TM)
    - See options for setting your name, going to server browser, starting a game
  - Server browser
  - Game
    - Chat
- Bots
  - TBD

**Next Steps:**
- TM research Django app structure
- TM start on splash page
- ZL diagram DB structure
- ZL define routes better