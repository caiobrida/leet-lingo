using LeetLingo.Api.Problems;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.ChangeTracking;

namespace LeetLingo.Api;

public class LeetLingoContext(DbContextOptions<LeetLingoContext> options) : DbContext(options)
{
    public const string TheConnectionStringItReads = "LeetLingo";

    public DbSet<Problem> Problems => Set<Problem>();

    protected override void OnModelCreating(ModelBuilder model)
    {
        var problems = model.Entity<Problem>();

        problems.HasIndex(problem => problem.Slug).IsUnique();

        problems
            .Property(problem => problem.TestCases)
            .HasColumnType("jsonb")
            .HasConversion(
                testCases => TestCases.AsOneDocument(testCases),
                document => TestCases.From(document),
                new ValueComparer<IReadOnlyList<TestCase>>(
                    (left, right) => left!.SequenceEqual(right!),
                    testCases => testCases.Aggregate(
                        testCases.Count,
                        (hash, testCase) => HashCode.Combine(hash, testCase)),
                    testCases => testCases.ToList()));

        problems.HasData(TheSeededCatalogue.Problems);
    }
}
