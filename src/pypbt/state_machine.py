from __future__ import annotations

from collections.abc import Sequence
import itertools
from typing import Any, NamedTuple, Optional, Protocol, Union


# Vamos a usar una representación típica de la máquina de estados:
# una tabla state/event.
#
# Para declarar la table en el código escribiremos por cada columna:
#
# ```
# Current State = (
#     (input, input_arg, next_state),
#     ...
# )
# ```
#
# En la notación matemática convencional, la tabla viene siendo la
# función delta.

CommandName = str
StateName = str
DeltaArg = Tuple[
    Union[CommandName, Sequence[CommandName], Ellipsis],
    'domain.Domain',
    StateName
]

class _DeltaDescriptor:
    def __init__(self, args: list[DeltaArg]):
        self.args = args

    def __set_name__(self, owner, name):
        if not type(owner) == type:
            raise TypeError(f"delta() must be declared in class scope")

        owner._StateMachine__table[name] = self.args

        
def delta(*args) -> _DeltaDescriptor:
    return _DeltaDescriptor(args)


class StateMachine:
    __table = {}
    _cmds = {}

    def __init_subclass__(cls):
        # Calculamos los conjuntos de nombres de cmds y states de la tabla
        table_cmd_names = set()
        table_state_names = set()
        for cmds, _, next_st_name in itertools.chain(cls.__table.values()):
            if type(cmds) == list:
                table_cmd_names.update(cmds)
            elif cmds != ...:
                table_cmd_names.add(cmds)
            table_state_names.add(next_st_name)

        # Avisar de las funciones `do_xxx` que no se usan
        #
        # Lanzar una excepción si la tabla contiene un cmd para el que
        # no hay función `do_cmd`
        cls_cmds = { name.removeprefix(prefix): getattr(cls, name)
                 for name in dir(cls) if name.startswith(prefix) }
        valid_cmd_names = set(cls_cmds.keys())
        if ... not in table_cmd_names:
            unused_cmds = valid_cmd_names - table_cmd_names
            for cmd in unused_cmds:
                print(f"WARNING: the command {cmd} is not used in the state machine {cls.__name__}")
        invalid_cmds = table_cmd_names - valid_cmd_names
        invalid_cmds.discard(...)
        if len(invalid_cmds) > 0:
            fun_names = ", ".join(f"do_{cmd}" for cmd in invalid_cmds)
            raise ValueError(f"Missing {fun_names} in {cls.__name__}")
        cls._cmds = cls_cmds
        
        # TODO: no sabemos qué estados son inicial o final, cómo
        #   hacemos para avisar si hay un estado inalcanzable o del que
        #   no se puede salir (sobre todo si es por culpa de un typo)
        

# El objetivo no es "programar" una máquina de estados, sino definir
# un modelo abstracto del sistema que se está probando (_SUT_). Por
# eso la forma de definir la máquina de estados es un tanto particular.
#
# El caso que nos ocupa es un SUT donde el resultado de cada acción
# (_command_) depende del resultado de las acciones anteriores, es
# decir, del estado en que se encuentra el SUT. Al mismo tiempo el SUT
# es demasiado complejo como para poder escribir propiedades
# convencionales. Lo que hacemos es definir un modelo abstracto del
# SUT, suficientemente sencillo como para escribir propiedades
# relevantes sobre él. El modelo que elegimos se basa en una máquina
# de estados que define:
#
#   - Los estados en que puede estar el SUT.
#
#   - Las acciones (commands) que se pueden realizar sobre el SUT.
#
#   - Los cambios de estado que provoca cada acción.
#
# Una vez definido el modelo, el SUT pasa a ser una caja negra/gris.
# Sobre el modelo calcularemos los cambios de estado que provocan una
# serie de transiciones elegidas al azar. Al mismo tiempo, por cada
# transición lanzaremos la acción correspondiente sobre el SUT y
# comprobaremos las propiedades que nos garantizan que el
# comportamiento del SUT es coherente con el definido en el modelo.
#
# Por tanto, además de la máquina de estados, también necesitaremos:
#
#   - Funciones que lanzan en el SUT las acciones representadas en la
#     máquina de estados.
#
#
# Transition = (from_state, to_state, cmd_name, cmd_args, cmd_result)
#
#
# > \delta is the state-transition function: δ : S × Σ → S
# > {\displaystyle \delta :S\times \Sigma \rightarrow S}
#
# DeltaPairs = (StateName, Sequence ([command] | ..., Maybe Domain, StateName)
#
# Aquí hay que tener en cuenta que el orden es relevante en la
# secuencia de posibles transiciones. Igual que las cláusulas en erlang.

class Mi6STMachine(StateMachine):
    STOPPED = delta(
        ('Fundar', None, 'STARTED'),
        (..., None, 'STOPPED'), # No parece buena idea, pero completa el ejemplo
    )
    
    STARTED = delta(
        ('Recrutar', (domain.Axente(), domain.Destino()), 'STARTED'),
        ('Disolver', None, 'STOPPED'),
        (..., None, 'STARTED'),  
        (('Fundar', 'Asignar_Mision'), None, 'STARTED'),  # WARNING, el comodín lo subsume     
    )

    
    def __init__(self):
        self.axentes = {}

        
    # guardas estúpidas, ya pueden estar en las transiciones
    def guard_STARTED(self, from_state, cmd_args) -> bool:
        return from_state not in STARTED

    def guard_function(self, to_state, from_state, cmd_args) -> bool:
        return from_state not in STOPPED
    

    def do_Fundar(self, cmd_args) -> Any:
        ...

    def do_Recrutrar(self, cmd_args) -> Any:
        ...

    def do_Asignar_Mision(self, cmd_args) -> Any:
        ...

    def do_Consultar_Estado(self, cmd_args) -> Any:
        ...

    def do_Disolver(self, cmd_args) -> Any:
        ...


    def predicate_Consultar_Estado(self, transition: Transition) -> bool:
        return self.axentes[transition.cmd_args] == transition.cmd_result


# STMRun(state_machine: StateMachine, initial_state, sut_factory: Callable[[], Any])
#
# El dominio STMRun es el conjunto de todas las secuencias de transiciones que se pueden
# dar en la máquina de estados, partiendo del estado indiciado.
#
# Cada secuencia de transisiones se representa como un `run`, que es
# un iterable de dicha secuencia.
#
# run = Iterable[Transistion]
#
# Obviously cada transición depende de las anteriores (eso que llaman
# estado).  Las transiciones se aplican a medida que se itera sobre
# ellas (de forma perezosa). Por cada transición podemos comprobar los
# predicados que consideremos oportunos.

@forall(run= STMRun(Echo, Echo.STOPPED, echo_factory))
def test_todo_esta_en_su_sitio(run):
    for transition in run:
        # Comprobamos los predicados definidos en la StateMachine
        # Si queremos comprobar otra cosa, pues adelante
        Echo.check(transition)
    # También podríamos hacer
    Echo.check(run)




















class _Name:
    _name = None

    def __str__(self):
        return self._name
    
    def __repr__(self):
        return f"{self._name} = {self.__class__.__name__}()"

    def __set_name__(self, owner, name):
        if not type(owner) == type:
            raise TypeError(f"{self.__class__.__name__} must be declared in class scope")
        self._name = f"{owner.__name__}.{name}"


class StateName(_Name)
    def __contains__(self, other):
        if type(other) == StateName:
            return other == self
        elif isinstance(other, State):
            return other._state_name == self
        else:
            return False

    @property
    def name(self) -> StateName:
        return self

    def replace(self, name) -> State:
        raise ValueError("Cannot change name in StateName")
    
        
class State(Protocol):
    name: StateName
    def replace(self, **kwargs) -> State:
        ...

    
class CommandName(_Name):
    def __call__(self, event: Union[Domain, Any]= None) -> Command:
        return Command(self, event)


class Command:
    def __init__(self, name: CommandName, event: Union[Domain, Any]= None):
        self.name: CommandName = name
        self._event: Union[Domain, Any] = event

    def events(self) -> Iterator:
        if not is_domain(self.event):
            yield self.event
        else:
            yield from self._event()




# Ejemplos

class EchoSTMachine(StateMachine):
    STOPPED = StateName()
    STARTED = StateName()

    Start = CommandName()
    Stop  = ComnnandName()
    Print = CommandName()

    transitions = {
        STOPPED: [
            (Start, None, STARTED)
        ],
        STARTED: [
            (Print, domain.String(), STARTED),
            (Stop, None, STOPPED)
        ],
    }

    def do_Print(self, event):
        ...

    def do_Start(self):
        ...

    def do_Stop(self):
        ...
        

class Mi6STMachine(StateMachine):
    STARTED = StateName()
    STOPPED = StateName()

    Fundar = CommandName()
    Recrutar = CommandName()
    Asignar_Mision = CommandName()
    Consultar_Estado = CommandName()
    Disolver = CommandName()

    transitions = {
        STOPPED: [
            (Fundar, None, STARTED),
            (..., None, STOPPED), # No parece buena idea, pero completa el ejemplo
        ],
        STARTED: [
            (Recrutar, (domain.Axente(), domain.Destino()), STARTED),
            (Disolver, None, STOPPED),
            (..., None, STARTED),  
            (Fundar | Asignar_Mision), None, STARTED),  # WARNING, el comodín lo subsume     
        ]


# El objetivo no es "programar" una máquina de estados, sino definir
# un modelo abstracto del sistema que se está probando (_SUT_). Por
# eso la forma de definir la máquina de estados es un tanto particular.
#
# El caso que nos ocupa es un SUT donde el resultado de cada acción
# (_command_) depende del resultado de las acciones anteriores, es
# decir, del estado en que se encuentra el SUT. Al mismo tiempo el SUT
# es demasiado complejo como para poder escribir propiedades
# convencionales. Lo que hacemos es definir un modelo abstracto del
# SUT, suficientemente sencillo como para escribir propiedades
# relevantes sobre él. El modelo que elegimos se basa en una máquina
# de estados que define:
#
#   - Los estados en que puede estar el SUT.
#
#   - Las acciones (commands) que se pueden realizar sobre el SUT.
#
#   - Los cambios de estado que provoca cada acción.
#
# Una vez definido el modelo, el SUT pasa a ser una caja negra/gris.
# Sobre el modelo calcularemos los cambios de estado que provocan una
# serie de transiciones elegidas al azar. Al mismo tiempo, por cada
# transición lanzaremos la acción correspondiente sobre el SUT y
# comprobaremos las propiedades que nos garantizan que el
# comportamiento del SUT es coherente con el definido en el modelo.
#
# Por tanto, además de la máquina de estados, también necesitaremos:
#
#   - Funciones que lanzan en el SUT las acciones representadas en la
#     máquina de estados.
#
#
# Transition = (from_state, to_state, cmd_name, cmd_args, cmd_result)
#
#
# > \delta is the state-transition function: δ : S × Σ → S
# > {\displaystyle \delta :S\times \Sigma \rightarrow S}
#
# DeltaPairs = (StateName, Sequence ([command] | ..., Maybe Domain, StateName)
#
# Aquí hay que tener en cuenta que el orden es relevante en la
# secuencia de posibles transiciones. Igual que las cláusulas en erlang.

class Mi6STMachine(StateMachine):
    STOPPED = delta(
        ('Fundar', None, 'STARTED'),
        (..., None, 'STOPPED'), # No parece buena idea, pero completa el ejemplo
    )
    
    STARTED = delta(
        ('Recrutar', (domain.Axente(), domain.Destino()), 'STARTED'),
        ('Disolver', None, 'STOPPED'),
        (..., None, 'STARTED'),  
        (('Fundar', 'Asignar_Mision'), None, 'STARTED'),  # WARNING, el comodín lo subsume     
    )

    
    def __init__(self):
        self.axentes = {}

        
    # guardas estúpidas, ya pueden estar en las transiciones
    def guard_STARTED(self, from_state, cmd_args) -> bool:
        return from_state not in STARTED

    def guard_function(self, to_state, from_state, cmd_args) -> bool:
        return from_state not in STOPPED
    

    def do_Fundar(self, cmd_args) -> Any:
        ...

    def do_Recrutrar(self, cmd_args) -> Any:
        ...

    def do_Asignar_Mision(self, cmd_args) -> Any:
        ...

    def do_Consultar_Estado(self, cmd_args) -> Any:
        ...

    def do_Disolver(self, cmd_args) -> Any:
        ...


    def predicate_Consultar_Estado(self, transition: Transition) -> bool:
        return self.axentes[transition.cmd_args] == transition.cmd_result


# STMRun(state_machine: StateMachine, initial_state, sut_factory: Callable[[], Any])
#
# El dominio STMRun es el conjunto de todas las secuencias de transiciones que se pueden
# dar en la máquina de estados, partiendo del estado indiciado.
#
# Cada secuencia de transisiones se representa como un `run`, que es
# un iterable de dicha secuencia.
#
# run = Iterable[Transistion]
#
# Obviously cada transición depende de las anteriores (eso que llaman
# estado).  Las transiciones se aplican a medida que se itera sobre
# ellas (de forma perezosa). Por cada transición podemos comprobar los
# predicados que consideremos oportunos.

@forall(run= STMRun(Echo, Echo.STOPPED, echo_factory))
def test_todo_esta_en_su_sitio(run):
    for transition in run:
        # Comprobamos los predicados definidos en la StateMachine
        # Si queremos comprobar otra cosa, pues adelante
        Echo.check(transition)
    # También podríamos hacer
    Echo.check(run)




################################################################################

class State(NamedTuple):
    name: StateName


def state(st: Union[StateName, State]) -> State:
    if isinstance(st, StateName):
        return State(st)
    else:
        return st


def _normalize(transition_list):
    return [ transition if type(transition) == tuple else (None, transition)
        for transition in transition_list
    ]


class StateMachine:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        print(cls, kwargs)
        cls.transitions = { st: _normalize(transition_list)
                            for st, transition_list in cls.transitions.items() }
        print(cls.transitions)

    def __setattr__(self, name, value):
        raise TypeError("Instances of StateMachine are inmutable")

    def __str__(self):
        return f"StateMachine:{self.__class__.__name__}"

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def get_transition(self, state: State) -> Optional[Transition]:
        transitions = self.transitions[state.name]
        for transition in _random.sample(transitions, k= len(transitions)):
            event_domain, next_state = transition
            guard = getattr(self, f"guard_{next_state}", None)
            if guard is None:
                return transition
            elif not is_domain(event_domain):
                event = event_domain
                if guard(event):
                    return Transition(event, next_state)
            else:
                dom = event_domain()
                # Si la transición tiene asociado un dominio, intentamos n veces
                # encontrar una muestra que cumpla la guarda
                for _, event in zip(range(100), dom):
                    if guard(event):
                        return Transition(event, next_state)
        return None

    def transition_to(self, from_state: State, transition: Transition) -> State:
        next_state = from_state._replace(name= transition.state_name)
        before = getattr(self, f"before_{str(state.name)}", None)
        if before is not None:
            next_state = before(next_state, transition.event)
        after = getattr(self, f"after_{str(state.name)}", None)
        if before is not None:
            next_state = after(next_state, transition.event)
        return next_state

    def do_sut_transition_to(self, sut: Any, from_state: State, transition: Transition) -> Any:
        command = getattr(self, f"do_command_to_{str(state.name)}", None)
        if command is None:
            raise RuntimeError(f"Cannot transition sut to {state.name}")
        return command(sut, from_state, transition.event)
    
    
class Transition(NamedTuple):
    event: Optional[Union[Domain, Any]]
    state_name: StateName
        

class FooState(State):
    field_1: int= 0
    field_2: str= ""

    def __init__(self, state_name: StateName):
        super().__init__(state_name)
        
    
class Foo(StateMachine):
    CREATED = StateName()
    PARTIAL = StateName()
    COMPLETE = StateName()

    transitions = {
        CREATED: [ ('domain.Int()', PARTIAL) ],
        PARTIAL: [ COMPLETE ],
    }

    def guard_function(self, state, event) -> bool:
        return state in self.CREATED or state in self.PARTIAL

    def before_transition(self, state, event) -> Foo:
        return data

    def after_transition(self, state, event) -> Foo:
        return data

    def do_transition(self, state, event):
        sut.do_something()


print("Creando")
stm = Foo()
print(stm)
#stm.field_1 = 7
#stm.transitions = {}
#stm.CREATED = 0
print()
st = FooState(stm.CREATED)
print(st in stm.CREATED)
print(st in stm.PARTIAL)
print(stm.CREATED in stm.CREATED)
stm2 = Foo()
print(stm2.CREATED in stm.CREATED)


class Echo(StateMachine):
    STOPPED = StateName()
    STARTED = StateName()

    START = CommandName()
    PRINT = CommandName()
    STOP = CommandName()
    
    transitions = {
        STARTED: [ (PRINT, domain.String()), (STOP, None) ],
        STOPPED: [ (START, None) ]
    }

"""
property "o servidor de echo imprime todo o que se lle manda", [:verb
       │ ose] do
   9   │     forall cmds in commands(__MODULE__) do
  10   │       trap_exit do
  11   │         kill_echo_if_alive()
  12   │         {history, state, result} = run_commands(__MODULE__, cmds)
  13   │ 
  14   │         (result == :ok)
  15   │         |> when_fail(
  16   │           IO.puts("""
  17   │           History: #{inspect(history, pretty: true)}
  18   │           State: #{inspect(state, pretty: true)}
  19   │           Result: #{inspect(result, pretty: true)}
  20   │           """)
  21   │         )
  22   │         |> aggregate(command_names(cmds))
  23   │       end
  24   │     end
  25   │   end
"""

# Estaría bien si pudiesemos poner el sut en cualquier estado arbitrario
#@forall(state= State(STMFoo))
#@forall(transition= lambda state: Transition(STMFoo, state))
#def test_o_servidor_rula(state, transition):
#    next_state = STMFoo.do_transition(state, transition, sut)
#    return STMFoo.check_sut_state(sut, next_state)


def echo_factory():
    pass


@forall(run= STMRun(Echo, Echo.STOPPED, echo_factory))
def test_o_sut_rula(run):
    for step in run:
        if step.is_error():
            return False
    return True


class STMRun(Domain):
    def __init__(self,
                 stm: StateMachine,
                 initial_state: Union[StateName, State],
                 sut_factory: Callable[[], Any]):
        self.stm = stm
        self.initial_state = state(initial_state)
        self.sut_factory = sut_factory

    def __iter__(self) -> Iterator:
        while True:
            yield self._one_run()

    def _one_run(self) -> Iterator[Step]:
        state = self.initial_state
        stm = self.stm
        sut = self.sut_factory()
        while True:
            transition = stm.get_transition(state)
            next_state = stm.transition_to(state, transition)
            sut = stm.do_sut_transition_to(sut, state, transition)

            # comparar sut y next_state
            # yield resultado

    def __str__(self):
        return f"STMRun({self.stm}, {self.initial_state}, {self.sut_factory})"
