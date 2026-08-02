using Microsoft.EntityFrameworkCore;

namespace LeetLingo.Api.Problems;

public static class TheCatalogue
{
    public static Task<ProblemAnswered?> ReadTheProblem(
        this LeetLingoContext catalogue,
        string slug) =>
        catalogue.Problems
            .AsNoTracking()
            .Where(problem => problem.Slug == slug)
            .Select(problem => new ProblemAnswered(
                problem.Slug,
                problem.Title,
                problem.Statement,
                problem.FunctionSignature,
                problem.TestCases))
            .SingleOrDefaultAsync();
}
