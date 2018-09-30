# aiotba
yet another wrapper for The Blue Alliance's API except this one uses `asyncio` because it magically makes everything 
faster, right?

also because there's an overcomplicated type hinting system so there's autocomplete on everything (except for the season
specific data structures, those are all just dicts lol and nobody cares about them _most_ of the time)

# example
```python
import asyncio
from aiotba import TBASession

async def main():
    ses = TBASession("tba apiv3 key here")
    poofs = await ses.team(254)
    print(poofs.nickname)

asyncio.run(main())
```
this lib follows closely to the endpoints of [APIv3](https://www.thebluealliance.com/apidocs/v3) and should cover just
about all of them except for the `simple` endpoints

# installation
`pip install aiotba`

# notes
all of this is on a provisional basis and large parts of the api could change at a moment's notice. this isn't "stable" 
yet so to speak.
