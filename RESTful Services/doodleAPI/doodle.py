from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()


class Vote(BaseModel):
    option: str


class Poll(BaseModel):
    name: str
    options: list[str]
    votes: dict[int, Vote] = {}


polls: dict[int, Poll] = {}


@app.get("/poll")
async def get_polls():
    return polls


@app.post("/poll")
async def create_poll(poll: Poll):
    poll_id = len(polls) + 1
    polls[poll_id] = poll
    return {"poll_id": poll_id, "poll": poll}


@app.get("/poll/{poll_id}")
async def get_poll(poll_id: int):
    if poll_id in polls:
        return polls[poll_id]
    else:
        content = {"message": "Poll not found"}
        return JSONResponse(status_code=404, content=content)


@app.put("/poll/{poll_id}")
async def update_poll(poll_id: int, poll: Poll):
    if poll_id in polls:
        polls[poll_id] = poll
        return {"poll_id": poll_id, "poll": poll}
    else:
        content = {"message": "Poll not found"}
        return JSONResponse(status_code=404, content=content)


@app.delete("/poll/{poll_id}")
async def delete_poll(poll_id: int):
    if poll_id in polls:
        del polls[poll_id]
        content = {"message": "Poll deleted"}
        return JSONResponse(status_code=200, content=content)
    else:
        content = {"message": "Poll not found"}
        return JSONResponse(status_code=404, content=content)


@app.get("/poll/{poll_id}/vote")
async def get_votes(poll_id: int):
    if poll_id in polls:
        return polls[poll_id].votes
    else:
        content = {"message": "Poll not found"}
        return JSONResponse(status_code=404, content=content)


@app.post("/poll/{poll_id}/vote")
async def cast_vote(poll_id: int, vote: Vote):
    if poll_id in polls:
        vote_id = len(polls[poll_id].votes) + 1
        polls[poll_id].votes[vote_id] = vote
        return {"vote_id": vote_id, "vote": vote}
    else:
        content = {"message": "Poll not found"}
        return JSONResponse(status_code=404, content=content)


@app.get("/poll/{poll_id}/vote/{vote_id}")
async def get_vote(poll_id: int, vote_id: int):
    if poll_id in polls:
        if vote_id in polls[poll_id].votes:
            return polls[poll_id].votes[vote_id]
        else:
            content = {"message": "Vote not found"}
            return JSONResponse(status_code=404, content=content)
    else:
        content = {"message": "Poll not found"}
        return JSONResponse(status_code=404, content=content)


@app.put("/poll/{poll_id}/vote/{vote_id}")
async def update_vote(poll_id: int, vote_id: int, vote: Vote):
    if poll_id in polls:
        if vote_id in polls[poll_id].votes:
            polls[poll_id].votes[vote_id] = vote
            return {"vote_id": vote_id, "vote": vote}
        else:
            content = {"message": "Vote not found"}
            return JSONResponse(status_code=404, content=content)
    else:
        content = {"message": "Poll not found"}
        return JSONResponse(status_code=404, content=content)


@app.delete("/poll/{poll_id}/vote/{vote_id}")
async def delete_vote(poll_id: int, vote_id: int):
    if poll_id in polls:
        if vote_id in polls[poll_id].votes:
            del polls[poll_id].votes[vote_id]
            content = {"message": "Vote deleted"}
            return JSONResponse(status_code=200, content=content)
        else:
            content = {"message": "Vote not found"}
            return JSONResponse(status_code=404, content=content)
    else:
        content = {"message": "Poll not found"}
        return JSONResponse(status_code=404, content=content)
