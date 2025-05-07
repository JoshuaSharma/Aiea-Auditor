:- dynamic conducts_electricity/1.
:- dynamic made_of/2.
:- dynamic material_type/2.

% Facts
material_type(metal, conducts_electricity).
material_type(insulator, does_not_conduct_electricity).
material_type(iron, metal).
made_of(nails, iron).

% Rules
conducts_electricity(X) :-
    made_of(X, Material),
    material_type(Material, Type),
    Type == conducts_electricity.

does_not_conduct_electricity(X) :-
    made_of(X, Material),
    material_type(Material, Type),
    Type == does_not_conduct_electricity.