using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace LeetLingo.Api.Migrations
{
    public partial class TheInitialCatalogue : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Problems",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Slug = table.Column<string>(type: "text", nullable: false),
                    Title = table.Column<string>(type: "text", nullable: false),
                    Statement = table.Column<string>(type: "text", nullable: false),
                    FunctionSignature = table.Column<string>(type: "text", nullable: false),
                    TestCases = table.Column<string>(type: "jsonb", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Problems", x => x.Id);
                });

            migrationBuilder.InsertData(
                table: "Problems",
                columns: new[] { "Id", "FunctionSignature", "Slug", "Statement", "TestCases", "Title" },
                values: new object[] { new Guid("8f14e45f-ceea-467a-9ba2-0f1b1a1c7d21"), "def solve(numbers: list[int], target: int) -> list[int]", "two-sum", "Given a list of integers and a target, return the indices of the two numbers that add up to the target.\n\nExactly one pair adds up to the target, and the same element may not be used twice. Return the two indices in ascending order.", "[{\"input\":[[2,7,11,15],9],\"expectedOutput\":[0,1]},{\"input\":[[3,2,4],6],\"expectedOutput\":[1,2]},{\"input\":[[3,3],6],\"expectedOutput\":[0,1]}]", "Two Sum" });

            migrationBuilder.CreateIndex(
                name: "IX_Problems_Slug",
                table: "Problems",
                column: "Slug",
                unique: true);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Problems");
        }
    }
}
