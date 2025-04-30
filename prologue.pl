
% Facts
person(gerald_jay_sussman).
person(random_computerscientist).
profession(gerald_jay_sussman, computer_scientist).
profession(random_computerscientist, computer_scientist).
profession(gerald_jay_sussman, professor).
affiliation(gerald_jay_sussman, mit).
well_known_for(gerald_jay_sussman, artificial_intelligence).
well_known_for(gerald_jay_sussman, computer_science_education).

% Co-authored book
coauthored(gerald_jay_sussman, sicp).
coauthor(hal_abelson, sicp).
book(sicp, "Structure and Interpretation of Computer Programs").
used_for(sicp, introductory_computer_science_courses).
emphasizes(sicp, programming_principles).
emphasizes(sicp, deep_understanding_of_programs).

% Contributions
contributed_to(gerald_jay_sussman, scheme_language).
scheme_language_description("a minimalist, multi-paradigm programming language in the Lisp family").

% Work and interests
work_field(gerald_jay_sussman, ai_development).
influential_person(gerald_jay_sussman, computer_science_education_practice).
interest(gerald_jay_sussman, electrical_engineering).

% Projects
worked_on(gerald_jay_sussman, digital_circuits_design).
worked_on(gerald_jay_sussman, vlsi_systems_design).
worked_on(yellow, red).

% Rules
is_ai_expert(Person) :-
    profession(Person, computer_scientist),
    well_known_for(Person, artificial_intelligence).
