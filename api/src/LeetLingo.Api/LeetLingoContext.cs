using LeetLingo.Api.Problems;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.ChangeTracking;

namespace LeetLingo.Api;

public class LeetLingoContext(DbContextOptions<LeetLingoContext> options) : DbContext(options)
{
    public const string TheDatabaseItReaches = "LeetLingo";

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
                    (left, right) =>
                        TestCases.AsOneDocument(left!) == TestCases.AsOneDocument(right!),
                    testCases => TestCases.AsOneDocument(testCases).GetHashCode(),
                    testCases => TestCases.From(TestCases.AsOneDocument(testCases))));

        problems.HasData(TheSeededCatalogue.Problems);
    }
}
