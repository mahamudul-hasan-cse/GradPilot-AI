"""University discovery seed data loader with Qdrant indexing."""

import argparse
import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.models.scholarship import Scholarship
from app.models.university import Program, University
from app.services.university_discovery import UniversityDiscoveryService

UNIVERSITY_SEED_DATA = [
    {
        "name": "Massachusetts Institute of Technology",
        "country": "United States",
        "city": "Cambridge",
        "website": "https://www.mit.edu",
        "ranking": 1,
        "tuition_fee": Decimal("58000"),
        "application_fee": Decimal("75"),
        "minimum_gpa": Decimal("3.7"),
        "minimum_ielts": Decimal("7.0"),
        "minimum_toefl": 90,
        "deadline": date(2026, 12, 15),
        "programs": ["MSc Computer Science", "MEng Electrical Engineering", "MBA"],
        "majors": ["Computer Science", "Engineering", "Business"],
        "scholarships_available": True,
        "description": "World-leading research university in science, engineering, and technology.",
    },
    {
        "name": "University of Oxford",
        "country": "United Kingdom",
        "city": "Oxford",
        "website": "https://www.ox.ac.uk",
        "ranking": 3,
        "tuition_fee": Decimal("42000"),
        "application_fee": Decimal("150"),
        "minimum_gpa": Decimal("3.6"),
        "minimum_ielts": Decimal("7.5"),
        "minimum_toefl": 110,
        "deadline": date(2027, 1, 10),
        "programs": ["MSc Computer Science", "MSc Financial Economics", "MSc Engineering Science"],
        "majors": ["Computer Science", "Economics", "Engineering"],
        "scholarships_available": True,
        "description": "Historic collegiate university with global academic reputation.",
    },
    {
        "name": "University of Toronto",
        "country": "Canada",
        "city": "Toronto",
        "website": "https://www.utoronto.ca",
        "ranking": 21,
        "tuition_fee": Decimal("45000"),
        "application_fee": Decimal("120"),
        "minimum_gpa": Decimal("3.3"),
        "minimum_ielts": Decimal("6.5"),
        "minimum_toefl": 93,
        "deadline": date(2027, 2, 1),
        "programs": ["MSc Applied Computing", "MSc Data Science", "MA Economics"],
        "majors": ["Computer Science", "Data Science", "Economics"],
        "scholarships_available": True,
        "description": "Canada's top research university with strong STEM and business programs.",
    },
    {
        "name": "University of Melbourne",
        "country": "Australia",
        "city": "Melbourne",
        "website": "https://www.unimelb.edu.au",
        "ranking": 33,
        "tuition_fee": Decimal("48000"),
        "application_fee": Decimal("100"),
        "minimum_gpa": Decimal("3.2"),
        "minimum_ielts": Decimal("6.5"),
        "minimum_toefl": 79,
        "deadline": date(2026, 11, 30),
        "programs": ["Master of IT", "Master of Data Science", "Master of Engineering"],
        "majors": ["Computer Science", "Data Science", "Engineering"],
        "scholarships_available": True,
        "description": "Leading Australian university known for research and employability.",
    },
    {
        "name": "Technical University of Munich",
        "country": "Germany",
        "city": "Munich",
        "website": "https://www.tum.de",
        "ranking": 37,
        "tuition_fee": Decimal("3000"),
        "application_fee": Decimal("0"),
        "minimum_gpa": Decimal("3.0"),
        "minimum_ielts": Decimal("6.5"),
        "minimum_toefl": 88,
        "deadline": date(2027, 5, 31),
        "programs": ["MSc Informatics", "MSc Robotics", "MSc Management"],
        "majors": ["Computer Science", "Robotics", "Business"],
        "scholarships_available": False,
        "description": "Top European technical university with low tuition and strong industry ties.",
    },
    {
        "name": "Arizona State University",
        "country": "United States",
        "city": "Tempe",
        "website": "https://www.asu.edu",
        "ranking": 156,
        "tuition_fee": Decimal("32000"),
        "application_fee": Decimal("70"),
        "minimum_gpa": Decimal("2.8"),
        "minimum_ielts": Decimal("6.0"),
        "minimum_toefl": 61,
        "deadline": date(2027, 3, 1),
        "programs": ["MS Computer Science", "MS Business Analytics", "MS Engineering"],
        "majors": ["Computer Science", "Business Analytics", "Engineering"],
        "scholarships_available": True,
        "description": "Large public research university with accessible admission standards.",
    },
    {
        "name": "University of Auckland",
        "country": "New Zealand",
        "city": "Auckland",
        "website": "https://www.auckland.ac.nz",
        "ranking": 68,
        "tuition_fee": Decimal("38000"),
        "application_fee": Decimal("100"),
        "minimum_gpa": Decimal("3.0"),
        "minimum_ielts": Decimal("6.5"),
        "minimum_toefl": 90,
        "deadline": date(2026, 12, 1),
        "programs": ["Master of Computer Science", "Master of Engineering Studies"],
        "majors": ["Computer Science", "Engineering"],
        "scholarships_available": True,
        "description": "New Zealand's highest-ranked university with strong international student support.",
    },
    {
        "name": "Northeastern University",
        "country": "United States",
        "city": "Boston",
        "website": "https://www.northeastern.edu",
        "ranking": 53,
        "tuition_fee": Decimal("56000"),
        "application_fee": Decimal("75"),
        "minimum_gpa": Decimal("3.2"),
        "minimum_ielts": Decimal("6.5"),
        "minimum_toefl": 79,
        "deadline": date(2027, 1, 15),
        "programs": ["MS Computer Science", "MS Data Analytics", "MS Project Management"],
        "majors": ["Computer Science", "Data Science", "Business"],
        "scholarships_available": True,
        "description": "Co-op focused university with excellent industry placement in Boston.",
    },
    {
        "name": "University of Manchester",
        "country": "United Kingdom",
        "city": "Manchester",
        "website": "https://www.manchester.ac.uk",
        "ranking": 32,
        "tuition_fee": Decimal("35000"),
        "application_fee": Decimal("0"),
        "minimum_gpa": Decimal("3.2"),
        "minimum_ielts": Decimal("6.5"),
        "minimum_toefl": 90,
        "deadline": date(2027, 7, 31),
        "programs": ["MSc Advanced Computer Science", "MSc AI", "MSc Finance"],
        "majors": ["Computer Science", "Artificial Intelligence", "Finance"],
        "scholarships_available": True,
        "description": "Russell Group university with strong CS and business faculties.",
    },
    {
        "name": "San Jose State University",
        "country": "United States",
        "city": "San Jose",
        "website": "https://www.sjsu.edu",
        "ranking": 280,
        "tuition_fee": Decimal("22000"),
        "application_fee": Decimal("70"),
        "minimum_gpa": Decimal("2.7"),
        "minimum_ielts": Decimal("6.0"),
        "minimum_toefl": 80,
        "deadline": date(2027, 4, 1),
        "programs": ["MS Software Engineering", "MS Computer Science"],
        "majors": ["Computer Science", "Software Engineering"],
        "scholarships_available": False,
        "description": "Affordable Silicon Valley university with strong tech industry connections.",
    },
    {
        "name": "University of British Columbia",
        "country": "Canada",
        "city": "Vancouver",
        "website": "https://www.ubc.ca",
        "ranking": 34,
        "tuition_fee": Decimal("42000"),
        "application_fee": Decimal("168"),
        "minimum_gpa": Decimal("3.3"),
        "minimum_ielts": Decimal("6.5"),
        "minimum_toefl": 90,
        "deadline": date(2027, 1, 15),
        "programs": ["MSc Computer Science", "Master of Data Science", "MBA"],
        "majors": ["Computer Science", "Data Science", "Business"],
        "scholarships_available": True,
        "description": "Top Canadian university on the Pacific coast with vibrant tech ecosystem.",
    },
    {
        "name": "Imperial College London",
        "country": "United Kingdom",
        "city": "London",
        "website": "https://www.imperial.ac.uk",
        "ranking": 6,
        "tuition_fee": Decimal("48000"),
        "application_fee": Decimal("80"),
        "minimum_gpa": Decimal("3.5"),
        "minimum_ielts": Decimal("7.0"),
        "minimum_toefl": 100,
        "deadline": date(2027, 1, 15),
        "programs": ["MSc Computing", "MSc AI", "MSc Finance"],
        "majors": ["Computer Science", "Artificial Intelligence", "Finance"],
        "scholarships_available": True,
        "description": "STEM-focused elite university in central London.",
    },
]


async def load_seed_data(*, force: bool = False, index_vectors: bool = True) -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(University).limit(1))
        if existing.scalar_one_or_none() and not force:
            print("Seed data already exists. Use --force to reload.")
            return

        if force:
            await session.execute(delete(Program))
            await session.execute(delete(University))
            await session.commit()

        universities: list[University] = []
        for data in UNIVERSITY_SEED_DATA:
            university = University(**data)
            university.search_text = university.build_search_text()
            session.add(university)
            universities.append(university)

        await session.flush()

        for university in universities:
            if university.programs:
                session.add(
                    Program(
                        university_id=university.id,
                        name=university.programs[0],
                        degree_type="Masters",
                        field_of_study=university.majors[0] if university.majors else None,
                        tuition_fee=university.tuition_fee,
                        tuition_currency="USD",
                        application_deadline=university.deadline,
                    )
                )

        scholarship_count = await session.execute(select(Scholarship).limit(1))
        if not scholarship_count.scalar_one_or_none():
            session.add_all(
                [
                    Scholarship(
                        title="Fulbright Foreign Student Program",
                        provider="U.S. Department of State",
                        country="United States",
                        amount=Decimal("50000"),
                        currency="USD",
                        description="Graduate study grants for international students in the U.S.",
                        eligibility="International students with strong academic records.",
                        degree_level="masters",
                        funding_type="full",
                        minimum_gpa=Decimal("3.2"),
                        minimum_ielts=Decimal("6.5"),
                        research_required=False,
                        work_experience_required_years=None,
                        eligible_nationalities=None,
                        eligible_majors=None,
                    ),
                    Scholarship(
                        title="Chevening Scholarships",
                        provider="UK Government",
                        country="United Kingdom",
                        amount=Decimal("40000"),
                        currency="GBP",
                        description="Fully funded scholarships for one-year master's degrees in the UK.",
                        eligibility="Outstanding emerging leaders with a bachelor's degree.",
                        degree_level="masters",
                        funding_type="full",
                        minimum_gpa=Decimal("3.0"),
                        minimum_ielts=Decimal("6.5"),
                        research_required=False,
                        work_experience_required_years=2,
                        eligible_nationalities=None,
                        eligible_majors=None,
                    ),
                ]
            )

        await session.commit()
        print(f"Loaded {len(universities)} universities.")

        if index_vectors:
            discovery = UniversityDiscoveryService(session)
            count = await discovery.index_all_universities()
            print(f"Indexed {count} universities in Qdrant.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Load university discovery seed data")
    parser.add_argument("--force", action="store_true", help="Delete and reload all universities")
    parser.add_argument("--no-index", action="store_true", help="Skip Qdrant vector indexing")
    args = parser.parse_args()
    asyncio.run(load_seed_data(force=args.force, index_vectors=not args.no_index))


if __name__ == "__main__":
    main()
