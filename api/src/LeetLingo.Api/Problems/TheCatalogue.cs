using Microsoft.EntityFrameworkCore;

namespace LeetLingo.Api.Problems;

public static class TheCatalogue
{
    public static Task<ProblemAnswered?> ReadTheProblem(
        this LeetLingoContext catalogue,
        string slug,
        CancellationToken givenUpOn) =>
        catalogue.Problems
            .Where(problem => problem.Slug == slug)
            .Select(problem => new ProblemAnswered(
                problem.Slug,
                problem.Title,
                problem.Statement,
                problem.FunctionSignature,
                problem.TestCases))
            .SingleOrDefaultAsync(givenUpOn);
}
