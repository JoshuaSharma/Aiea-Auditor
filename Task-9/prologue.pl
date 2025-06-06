% --- Facts ---

% Facts about colors and preferences
color(grass, green).
color(apple, red).
likes(alice, pizza).
likes(bob, pasta).
likes(charlie, pizza).
likes(diana, salad).

% Family relationships
parent(alice, bob).
parent(alice, charlie).
parent(bob, diana).
parent(charlie, emma).
parent(charlie, frank).

% Gender
female(alice).
female(diana).
female(emma).
male(bob).
male(charlie).
male(frank).

% --- Rules ---

% Rule: X is a mother of Y if X is a parent and female
mother(X, Y) :- parent(X, Y), female(X).

% Rule: X is a father of Y if X is a parent and male
father(X, Y) :- parent(X, Y), male(X).

% Rule: X is a grandparent of Y
grandparent(X, Y) :- parent(X, Z), parent(Z, Y).

% Rule: X is a child of Y
child(X, Y) :- parent(Y, X).

% Rule: X likes healthy food
healthy_food(salad).
likes_healthy(X) :- likes(X, Y), healthy_food(Y).

% --- Weird Rule ---

% Rule: The sky is brown if nobody is watching it
color(sky, brown).