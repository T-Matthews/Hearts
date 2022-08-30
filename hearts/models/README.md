## Data

### Example queries:

**Start a new game**
```python
Game.objects.create(player_1=player)
```

**Get list of ongoing games**
```python
Game.objects.filter(winning_player_id__isnull=True)
```

**Join a game**
```python
# Get game and make sure it's in progress.
game = Game.objects.get(id=game_id)
if game.is_in_progress:
    # Take over a spot currently occupied by a bot.
    for i in range(1, 5):
        if getattr(game, f'player_{i}').bot:
            setattr(game, f'player_{i}', player)
            game.save()
            break
```

**Get current hand**
```python
deal = Deal.objects.filter(game_id=game_id).latest('created_at')
PlayerCard.objects.filter(player=player, deal=deal, trick_id__isnull=True)
```

**Get current trick**
```python
deal = Deal.objects.filter(game_id=game_id).latest('created_at')
trick = Trick.objects.filter(deal=deal).latest('created_at')
```

**Play card**
```python
card = Card.objects.get(player=player, id=card_id)
card.trick_id = trick_id
card.save()
```

**Get pass direction**
```python
direction = [
    'left',
    'right',
    'forward',
    None,
][Deal.objects.filter(game_id=game_id).count() % 4]
```

**Get is hearts broken**
```python
Card.objects.filter(deal_id=deal_id, trick_id__isnull=False, suit=HEARTS).exists()
```

**Deal hand**
```python
shuffled = random.shuffle(cards)
index = 0
while len(cards) > 0:
    card = cards.pop()
    player_attr = f'player_{index % 4}'
    data = {
        'game': game,
        'suit': card.suit,
        'value': card.value,
        player_attr: getattr(game, player_attr),
    }
    Card.objects.create(**data)
    index += 1
```
