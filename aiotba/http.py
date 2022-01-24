import aiohttp
import time

from .models import *


def convert_team_key(value):
    if isinstance(value, TeamSimple):
        return value.key
    value = str(value)
    if value.startswith("frc"):
        return value
    else:
        return "frc" + value


def convert_key(value):
    if hasattr(value, "key"):
        return value.key
    return str(value)


def _get_expire_time(v):
    for k in v.split(","):
        k = k.strip()
        if k.startswith("max-age="):
            return time.time() + int(k[8:])


class AioTBAError(Exception):
    pass


class TBASession:
    def __init__(self, key: str, aiohttp_session=None, cache=True, max_cache=500):
        self.key = key
        self.cache_enabled = cache
        self.cache = {}
        self.max_cache = max_cache
        self.session = aiohttp.ClientSession() if not aiohttp_session else aiohttp_session

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    def prune_cache(self):
        if not self.cache_enabled:
            return
        kill = []
        for endpoint, (exp_time, etag, data) in self.cache.items():
            if exp_time < time.time():
                kill.append(endpoint)
        for k in kill:
            del self.cache[k]

    async def close(self):
        await self.session.close()

    async def req(self, endpoint: str, model):
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        data = None

        headers = {"X-TBA-Auth-Key": self.key}
        if endpoint in self.cache: # wont fire if cache not enabled as cache will be stuck empty
            exp_time, etag, data = self.cache[endpoint]
            headers["If-None-Match"] = etag
            if time.time() < exp_time:
                return to_model(data, model)
            # if the cached entry is stale then we don't bother deleting because it's about to update

        response = await self.session.get("https://www.thebluealliance.com/api/v3" + endpoint, headers=headers)
        async with response:
            if response.status == 200:
                data = await response.json()
                if self.cache_enabled:
                    if len(self.cache) > self.max_cache:
                        self.prune_cache()
                    self.cache[endpoint] = (_get_expire_time(response.headers["Cache-Control"]), response.headers['ETag'], data)

            elif response.status == 304:
                # cache oddity, probably some race condition or dsynched clocks or something stupid
                pass
            else:
                raise AioTBAError(f"Request to {endpoint} failed with {response.status} {response.reason}")

            return to_model(data, model)

    async def status(self) -> APIStatus:
        return await self.req('/status', APIStatus)

    async def teams(self, page=None, year=None, keys_only=False) -> Union[List[Team], List[str]]:
        base = "/teams"
        if year:
            base += f"/{year}"

        if keys_only:
            get_page = lambda n: self.req(base + f"/{n}/keys", List[str])
        else:
            get_page = lambda n: self.req(base + f"/{n}", List[Team])

        if page is not None:
            return await get_page(page)
        else:
            res = []
            for i in range(100): # unlikely to have this many pages tbh, its here as a failsafe
                page = await get_page(i)
                if not page:
                    break
                res += page
            return res

    async def team(self, team) -> Team:
        team_key = convert_team_key(team)
        return await self.req(f"/team/{team_key}", Team)

    async def team_years_participated(self, team) -> List[int]:
        team_key = convert_team_key(team)
        return await self.req(f"/team/{team_key}/years_participated", List[int])

    async def team_districts(self, team) -> List[District]:
        team_key = convert_team_key(team)
        return await self.req(f"/team/{team_key}/districts", List[District])

    async def team_robots(self, team) -> List[TeamRobot]:
        team_key = convert_team_key(team)
        return await self.req(f"/team/{team_key}/robots", List[TeamRobot])

    async def team_events(self, team, year=None, keys_only=False) -> Union[List[Event], List[str]]:
        team_key = convert_team_key(team)
        base = f"/team/{team_key}/events"
        if year is not None:
            base += f"/{year}"
        if keys_only:
            return await self.req(base + "/keys", List[str])
        else:
            return await self.req(base, List[Event])

    async def team_event_statuses(self, team, year) -> Dict[str, TeamEventStatus]:
        team_key = convert_team_key(team)
        return await self.req(f"/team/{team_key}/events/{year}/statuses", Dict[str, TeamEventStatus])

    async def team_event_matches(self, team, event, keys_only=False) -> Union[List[Match], List[str]]:
        team_key = convert_team_key(team)
        event_key = convert_key(event)
        if keys_only:
            return await self.req(f"/team/{team_key}/event/{event_key}/matches/keys", List[str])
        else:
            return await self.req(f"/team/{team_key}/event/{event_key}/matches", List[Match])

    async def team_event_awards(self, team, event) -> List[Award]:
        team_key = convert_team_key(team)
        event_key = convert_key(event)
        return await self.req(f"/team/{team_key}/event/{event_key}/awards", List[Award])

    async def team_event_status(self, team, event) -> TeamEventStatus:
        team_key = convert_team_key(team)
        event_key = convert_key(event)
        return await self.req(f"/team/{team_key}/event/{event_key}/status", TeamEventStatus)

    async def team_awards(self, team, year=None) -> List[Award]:
        team_key = convert_team_key(team)
        base = f"/team/{team_key}/awards"
        if year is not None:
            base += f"/{year}"
        return await self.req(base, List[Award])

    async def team_matches(self, team, year, keys_only=False) -> Union[List[Match], List[str]]:
        team_key = convert_team_key(team)
        if keys_only:
            return await self.req(f"/team/{team_key}/matches/{year}/keys", List[str])
        else:
            return await self.req(f"/team/{team_key}/matches/{year}", List[Match])

    async def team_media(self, team, year=None, tag=None) -> List[Media]:
        team_key = convert_team_key(team)
        base = f"/team/{team_key}/media"
        if not (year or tag):
            raise AioTBAError("At least one of {year, tag} must be specified!")
        if tag is not None:
            base += f"/tag/{tag}"
        if year is not None:
            base += f"/{year}"
        return await self.req(base, List[Media])

    async def team_social_media(self, team) -> List[Media]:
        team_key = convert_team_key(team)
        return await self.req(f"/team/{team_key}/social_media", List[Media])

    # /event/ endpoints
    async def events(self, year, keys_only=False) -> Union[List[Event], List[str]]:
        if keys_only:
            return await self.req(f"/events/{year}/keys", List[str])
        else:
            return await self.req(f"/events/{year}", List[Event])

    async def event(self, event_key) -> Event:
        event_key = convert_key(event_key)
        return await self.req(f"/event/{event_key}", Event)

    async def event_alliances(self, event) -> List[EliminationAlliance]:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/alliances", List[EliminationAlliance])

    async def event_insights(self, event) -> EventInsights:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/insights", EventInsights)

    async def event_oprs(self, event) -> EventOPRs:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/oprs", EventOPRs)

    async def event_predictions(self, event) -> EventPredictions:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/predictions", EventPredictions)

    async def event_rankings(self, event) -> EventRankings:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/rankings", EventRankings)

    async def event_district_points(self, event) -> EventDistrictPoints:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/district_points", EventDistrictPoints)

    async def event_teams(self, event, keys_only=False) -> Union[List[Team], List[str]]:
        event_key = convert_key(event)
        if keys_only:
            return await self.req(f"/event/{event_key}/teams/keys", List[str])
        else:
            return await self.req(f"/event/{event_key}/teams", List[Team])

    async def event_teams_statuses(self, event) -> Dict[str, TeamEventStatus]:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/teams/statuses", Dict[str, TeamEventStatus])

    async def event_matches(self, event, keys_only=False) -> Union[List[Team], List[str]]:
        event_key = convert_key(event)
        if keys_only:
            return await self.req(f"/event/{event_key}/matches/keys", List[str])
        else:
            return await self.req(f"/event/{event_key}/matches", List[Team])

    async def event_matches_timeseries(self, event) -> List[str]:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/matches/timeseries", List[str])

    async def event_awards(self, event) -> List[Award]:
        event_key = convert_key(event)
        return await self.req(f"/event/{event_key}/awards", List[Award])

    # /match endpoints
    async def match(self, match) -> Match:
        match_key = convert_key(match)
        return await self.req(f"/match/{match_key}", Match)

    async def match_timeseries(self, match) -> List[dict]:
        match_key = convert_key(match)
        return await self.req(f"/match/{match_key}/timeseries", List[dict])

    async def districts(self, year) -> List[District]:
        return await self.req(f"/districts/{year}", List[District])

    async def district_events(self, district, keys_only=False) -> Union[List[Event], List[str]]:
        district_key = convert_key(district)
        if keys_only:
            return await self.req(f"/district/{district_key}/events/keys", List[str])
        else:
            return await self.req(f"/district/{district_key}/events", List[Event])

    async def district_teams(self, district, keys_only=False) -> Union[List[Team], List[str]]:
        district_key = convert_key(district)
        if keys_only:
            return await self.req(f"/district/{district_key}/teams/keys", List[str])
        else:
            return await self.req(f"/district/{district_key}/teams", List[Team])

    async def district_rankings(self, district) -> List[DistrictRanking]:
        district_key = convert_key(district)
        return await self.req(f"/district/{district_key}/rankings", List[DistrictRanking])
