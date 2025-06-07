person(alice).
person(bob).
person(charlie).
person(diana).
person(emma).
person(frank).
watching_sky(alice) :- false.
watching_sky(bob) :- false.
watching_sky(charlie) :- false.
watching_sky(diana) :- false.
watching_sky(emma) :- false.
watching_sky(frank) :- false.
color(sky, brown) :- \+ watching_sky(_).
is_sky_brown :- color(sky, brown).