# api

The HTTP API — users, problems, submissions. C# and ASP.NET Core on .NET 10, Minimal APIs.

One project, never projects by layer — as concerns arrive they become folders inside it. This mirrors `/executor`, which is one package with modules. The API deliberately has no ability to execute submitted code: it delegates to the executor over HTTP and stores what comes back.

It requires the .NET 10 SDK or later, pinned in `global.json`.

## Commands

Run from this directory. Both act on `LeetLingo.slnx`, the only solution here.

| | |
| --- | --- |
| Build | `dotnet build` |
| Test | `dotnet test` |
| Run | `dotnet run --project src/LeetLingo.Api` |

## Layout

```
api/
  src/LeetLingo.Api/          the service
  tests/LeetLingo.Api.Tests/  the suite
```

Tests drive the API in process over real HTTP through `WebApplicationFactory`, with real dependency injection. They never call a handler directly, and test names are sentences, as they are throughout `/executor`.
