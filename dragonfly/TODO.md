[x] Support events
[ ] Network
    [x] TCP
    [ ] UDP
    [ ] TCP w/ datagrams
[ ] Make pause plugin to pause events + other sources (network isn't an event source, is it?) - possibly make it event
    ("network", "peer_name", ...)?
[x] Make entity API more component-like 

## String
[x] Startswith
[ ] Strip
[x] Replace
[ ] Split
[ ] Is [alpha, alphanum ...] PULL out bool

## Numeric
[x] Abs

## Complex
[x] Real
[x] Imag
[x] Conjugate

[x] Maybe have List, tuple, ... dicts
~~[ ] Make list, tuple etc pull in container~~
[x] Dict has get/set item {pull in}, view (keys, items, values), pop, setdefault, get

[ ] Read File [PUSH|lines, length, ...]
[ ] Write File # Maybe both of these replace input/print, and we optionally allow stdin? (advanced mode?)

[ ] Call {meta} - input args, output optional return result
[ ] Remove panda and blender from app/
    
[ ] Add kinematics (acceleration) (high priority)
[ ] Make Vector, Euler, Quaternion (...) types operable (add, subtract)
[ ] Support transformation matrices
[ ] Add sound
[ ] Add animation
[x] Min/max
[x] Constrain

[ ] Add FSM - use plugins to expose parent state machine for (goto) provide and transition events
## Spyder GUI
[ ] Use Spyder to generate all params
[ ] Use Spyder for colour type (hsv, rgb etc)
[ ] Reevaluate separating hives