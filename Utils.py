from opcua import ua

def changeState(stateOld, stateNew):
    stateOldId = stateOld.get_child(["Id"])
    stateOld.set_value(stateNew.get_display_name())
    stateOldId.set_value(stateNew.nodeid)

def changeTransition(transitionOld, transitionNew):
    transitionOldId = transitionOld.get_child(["Id"])
    transitionOld.set_value(transitionNew.get_display_name())
    transitionOldId.set_value(transitionNew.nodeid)

def generate_event(fsm, parent, event, message, severity):
    eventGen = fsm.server.get_event_generator(event, parent)
    eventGen.event.Message = ua.LocalizedText(message)
    eventGen.event.Severity = severity
    eventGen.trigger()

def create_references_transition(fsm, transitionid, methodid, eventtypeid, statefromid, statetoid):
    create_reference(fsm, False, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasCause)), methodid, ua.NodeClass.Object, transitionid)
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasCause)), transitionid, ua.NodeClass.Method, methodid)
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.FromState)), transitionid, ua.NodeClass.Object, statefromid)
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.ToState)), transitionid, ua.NodeClass.Object, statetoid)
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasEffect)), transitionid, ua.NodeClass.DataType, eventtypeid)

    # ua.NodeId.from_string("i=" + str(ua.ObjectIds.ProgramStateMachineType_Resume))
    # self.create_reference(True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasTypeDefinition)), methodid, ua.NodeClass.DataType, methoddefinitionid)


def create_reference(fsm, IsForward=True, ReferenceTypeId=None, SourceNodeId=None, TargetNodeClass=None, TargetNodeId=None):
    refs = []
    ref = ua.AddReferencesItem()
    ref.IsForward = IsForward
    ref.ReferenceTypeId = ReferenceTypeId
    ref.SourceNodeId = SourceNodeId
    ref.TargetNodeClass = TargetNodeClass
    ref.TargetNodeId = TargetNodeId
    refs.append(ref)
    fsm.nodeManagmentService.add_references(refs)

def get_elements_transition(fsm, cause_string, parent, stateCurrentNodeId):
    method = fsm.server.get_node(parent.to_string()).get_child([cause_string])

    transitions = method.get_references(refs=ua.ObjectIds.HasCause, direction=ua.BrowseDirection.Inverse)
    transition = None
    fromState = None
    for trans in transitions:
        transitionTmp = fsm.server.get_node(trans.NodeId)
        fromStateTmp = transitionTmp.get_children(refs=ua.ObjectIds.FromState, nodeclassmask=ua.NodeClass.Object)[0]
        print(transitionTmp)
        print(fromStateTmp)
        if stateCurrentNodeId == fromStateTmp.nodeid:
            transition = transitionTmp
            fromState = fromStateTmp
            break

    toState = transition.get_children(refs=ua.ObjectIds.ToState, nodeclassmask=ua.NodeClass.Object)[0]
    effect = transition.get_children(refs=ua.ObjectIds.HasEffect, nodeclassmask=ua.NodeClass.DataType)[0]

    # self.generate_event(parent, effect, "machine error", 500)

    return transition, fromState, toState, effect

def generate_method(fsm, parent, cause_string):
    # try:
    # currentState = parent.get_children(refs=ua.ObjectIds.ProgramStateMachineType_CurrentState, nodeclassmask=ua.NodeClass.DataType)[0]
    currentState = fsm.server.get_node(parent.to_string()).get_child(["CurrentState"])  # FIXME
    #lastTransition = fsm.server.get_node(parent.to_string()).get_child(["LastTransition"])  # FIXME
    currentStateId = currentState.get_child(["Id"])
    transition, fromState, toState, effect = get_elements_transition(fsm,cause_string, parent, currentStateId.get_value())
    changeState(currentState, toState)
    #changeTransition(lastTransition, transition)

    # except Exception as ex:
    # self.generate_event(parent, self.server.get_node(ua.ObjectIds.ProgramTransitionEventType), "Error to generate method "+cause_string, 111)
    # raise utils.ServiceError(ua.StatusCodes.BadMethodInvalid)


def generate_node_set(fsm):
    # Events Type
    programTransitionEventType = fsm.server.get_node(ua.ObjectIds.ProgramTransitionEventType)

    # Crear Referencias
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasNotifier)), fsm.server.get_server_node().nodeid, ua.NodeClass.Object, fsm.folder.nodeid)
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasNotifier)), fsm.folder.nodeid, ua.NodeClass.Object, fsm.scale.nodeid)
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasEventSource)), fsm.scale.nodeid, ua.NodeClass.Object, fsm.simulation.nodeid)

    # Transiciones
    for transition in find_nodes_by_types(fsm.simulation, fsm.server.get_node(ua.ObjectIds.TransitionType)):
        # Se crea la variable con el nombre de cada transicion
        exec("fsm.transition" + transition.get_browse_name().Name + " = " + "transition")

    for transition in find_nodes_by_types(fsm.subStateMachine, fsm.server.get_node(ua.ObjectIds.TransitionType)):
        # Se crea la variable con el nombre de cada transicion
        exec("fsm.subTransition" + transition.get_browse_name().Name + " = " + "transition")

    """"
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasTypeDefinition)), fsm.methodStart, ua.NodeClass.Variable, ua.NodeId.from_string("i=" + str(ua.ObjectIds.ProgramStateMachineType_Start)))
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasTypeDefinition)), fsm.methodResume, ua.NodeClass.Variable, ua.NodeId.from_string("i=" + str(ua.ObjectIds.ProgramStateMachineType_Resume)))
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasTypeDefinition)), fsm.methodHalt, ua.NodeClass.Variable, ua.NodeId.from_string("i=" + str(ua.ObjectIds.ProgramStateMachineType_Halt)))
    create_reference(fsm, True, ua.NodeId.from_string("i=" + str(ua.ObjectIds.HasTypeDefinition)), fsm.methodReset, ua.NodeClass.Variable, ua.NodeId.from_string("i=" + str(ua.ObjectIds.ProgramStateMachineType_Reset)))"""

    create_references_transition(fsm, fsm.transitionReadyToRunning.nodeid, fsm.methodStart.nodeid, programTransitionEventType.nodeid, fsm.stateReady.nodeid, fsm.stateRunning.nodeid)
    create_references_transition(fsm, fsm.transitionReadyToHalted.nodeid, fsm.methodHalt.nodeid, programTransitionEventType.nodeid, fsm.stateReady.nodeid, fsm.stateHalted.nodeid)
    create_references_transition(fsm, fsm.transitionHaltedToReady.nodeid, fsm.methodReset.nodeid, programTransitionEventType.nodeid, fsm.stateHalted.nodeid, fsm.stateReady.nodeid)
    create_references_transition(fsm, fsm.transitionRunningToSuspended.nodeid, fsm.methodSuspend.nodeid, programTransitionEventType.nodeid, fsm.stateRunning.nodeid, fsm.stateSuspended.nodeid)
    create_references_transition(fsm, fsm.transitionRunningToHalted.nodeid, fsm.methodHalt.nodeid, programTransitionEventType.nodeid, fsm.stateRunning.nodeid, fsm.stateHalted.nodeid)
    create_references_transition(fsm, fsm.transitionSuspendedToHalted.nodeid, fsm.methodHalt.nodeid, programTransitionEventType.nodeid, fsm.stateSuspended.nodeid, fsm.stateHalted.nodeid)
    create_references_transition(fsm, fsm.transitionSuspendedToRunning.nodeid, fsm.methodResume.nodeid, programTransitionEventType.nodeid, fsm.stateSuspended.nodeid, fsm.stateRunning.nodeid)

    create_references_transition(fsm, fsm.subTransitionFillingToDumping.nodeid, fsm.methodDump.nodeid, programTransitionEventType.nodeid, fsm.subStateFilling.nodeid, fsm.subStateDumping.nodeid)
    create_references_transition(fsm, fsm.subTransitionFillingToFilling.nodeid, fsm.methodFill.nodeid, programTransitionEventType.nodeid, fsm.subStateFilling.nodeid, fsm.subStateFilling.nodeid)
    create_references_transition(fsm, fsm.subTransitionDumpingToDumping.nodeid, fsm.methodDump.nodeid, programTransitionEventType.nodeid, fsm.subStateDumping.nodeid, fsm.subStateDumping.nodeid)
    create_references_transition(fsm, fsm.subTransitionDumpingToFilling.nodeid, fsm.methodFill.nodeid, programTransitionEventType.nodeid, fsm.subStateDumping.nodeid, fsm.subStateFilling.nodeid)

def find_nodes_by_types(node, type_to_find):
    """
    Search a nodes children for nodes of a specific object type
    :param node: Parent node which will be searched
    :param type_to_find: Object type node to find
    :return: List of nodes that match the desired object type
    """
    found_nodes = []
    for child in node.get_children():
        if child.get_type_definition() == type_to_find.nodeid:
            found_nodes.append(child)

    return found_nodes

