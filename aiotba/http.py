import aiohttp
import time

from .models import *


class AioTBAError(Exception):
    pass


class TBASession:
    def __init__(self, key: str, cache=True, max_cache=500):
        self.key = key
        self.cache_enabled = cache
        self.cache = {}
        self.max_cache = max_cache
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    def _get_expire_time(self, v):
        for k in v.split(","):
            k = k.strip()
            if k.startswith("max-age="):
                return time.time() + int(k[8:])

    def prune_cache(self):
        if not self.cache_enabled:
            return
        kill = []
        for endpoint, (exp_time, last_modified, data) in self.cache.items():
            if exp_time < time.time():
                kill.append(endpoint)
        for k in kill:
            del self.cache[k]

    def convert_team_key(self, value):
        if isinstance(value, TeamSimple):
            return value.key
        value = str(value)
        if value.startswith("frc"): return value
        else: return "frc" + value

    def convert_event_key(self, value):
        if isinstance(value, EventSimple):
            return value.key
        return str(value)

    async def close(self):
        await self.session.close()

    async def req(self, endpoint: str, model):
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        data = None

        headers = {"X-TBA-Auth-Key": self.key}
        if endpoint in self.cache: # wont fire if cache not enabled as cache will be stuck empty
            exp_time, last_modified, data = self.cache[endpoint]
            headers["If-Modified-Since"] = last_modified
            if time.time() < exp_time:
                return model.convert(data)

        response = await self.session.get("https://www.thebluealliance.com/api/v3" + endpoint, headers=headers)
        async with response:
            if response.status == 200:
                data = await response.json()
                if self.cache_enabled:
                    if len(self.cache) > self.max_cache:
                        self.prune_cache()
                    self.cache[endpoint] = (self._get_expire_time(response.headers["Cache-Control"]), response.headers["Last-Modified"], data)

            elif response.status == 304:
                # cache oddity
                pass
            else:
                raise AioTBAError(f"Request to {endpoint} failed with {response.status} {response.reason}")

            return model.convert(data)
    """
    status
    /teams/[year]/{page}/[keys]
    /team/
    """
    async def status(self):
        return await self.req('/status', APIStatus())

    async def teams(self, page=None, year=None, keys_only=False):
        base = "/teams"
        if year:
            base += f"/{year}"

        if keys_only:
            get_page = lambda n: self.req(base + f"/{n}/keys", Array(Field(str)))
        else:
            get_page = lambda n: self.req(base + f"/{n}", Array(Team()))

        if page is not None:
            return await get_page(page)
        else:
            res = []
            for i in range(100): # unlikely to have this many pages tbh, its here as a failsafe
                page = await get_page(i)
                if not page: break
                res += page
            return res

    async def team(self, team):
        team_key = self.convert_team_key(team)
        return await self.req(f"/team/{team_key}", Team())

    async def team_years_participated(self, team):
        team_key = self.convert_team_key(team)
        return await self.req(f"/team/{team_key}/years_participated", Array(Field(int)))

    async def team_districts(self, team):
        team_key = self.convert_team_key(team)
        return await self.req(f"/team/{team_key}/districts", Array(District()))

    async def team_robots(self, team):
        team_key = self.convert_team_key(team)
        return await self.req(f"/team/{team_key}/robots", Array(TeamRobot()))

    async def team_events(self, team, year=None, keys_only=False):
        team_key = self.convert_team_key(team)
        base = f"/team/{team_key}/events"
        if year is not None:
            base += f"/{year}"
        if keys_only:
            return await self.req(base + "/keys", Array(Field(str)))
        else:
            return await self.req(base, Array((Event())))

    async def team_event_statuses(self, team, year):
        team_key = self.convert_team_key(team)
        return await self.req(f"/team/{team_key}/events/{year}/statuses", Dict(Field(str), TeamEventStatus()))

    async def team_event_matches(self, team, event, keys_only=False):
        team_key = self.convert_event_key(team)
        event_key = self.convert_event_key(event)
        if keys_only:
            return await self.req(f"/team/{team_key}/event/{event_key}/matches/keys", Array(Field(str)))
        else:
            return await self.req(f"/team/{team_key}/event/{event_key}/matches", Array(Match()))

    async def team_event_awards(self, team, event):
        team_key = self.convert_event_key(team)
        event_key = self.convert_event_key(event)
        return await self.req(f"/team/{team_key}/event/{event_key}/awards", Array(Award()))

    async def team_event_status(self, team, event):
        team_key = self.convert_event_key(team)
        event_key = self.convert_event_key(event)
        return await self.req(f"/team/{team_key}/event/{event_key}/status", TeamEventStatus())

    async def team_awards(self, team, year=None):
        team_key = self.convert_event_key(team)
        base = f"/team/{team_key}"
        if year is not None:
            base += f"/{year}"
