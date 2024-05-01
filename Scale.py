import time, random
import threading
import Utils

from opcua.server.address_space import NodeManagementService
from opcua import ua, uamethod

class HandlerStateMachine(object):
	def __init__(self, fsm):
		self.fsm = fsm

	"""
	Subscription Handler. To receive events from server for a subscription
	"""
	def datachange_notification(self, node, val, data):
		# esta seccion de codigo es utilizada por un cliente escrito en node-re
		# el cual no tiene soporte para la llamada de metodos
		# por lo que se usa una variable y cuando esta tenga valor invoque al metodo
		# que indica la variables
		if (self.fsm.methodToExecute.get_value() != "" and self.fsm.methodToExecute.get_value() != None):
			if (self.fsm.methodToExecute.get_value() == "Start"):
				self.fsm.simulation.call_method(self.fsm.methodStart.nodeid)
			elif (self.fsm.methodToExecute.get_value() == "Reset"):
				self.fsm.simulation.call_method(self.fsm.methodReset.nodeid)
			elif (self.fsm.methodToExecute.get_value() == "Resume"):
				self.fsm.simulation.call_method(self.fsm.methodResume.nodeid)
			elif (self.fsm.methodToExecute.get_value() == "Suspend"):
				self.fsm.simulation.call_method(self.fsm.methodSuspend.nodeid)
			elif (self.fsm.methodToExecute.get_value() == "Halt"):
				self.fsm.simulation.call_method(self.fsm.methodHalt.nodeid)
			self.fsm.methodToExecute.set_value(None)

		print("Python: New data change event", node, val)

	def event_notification(self, event):
		print("Python: New event", event.EventType)


class ProgramFiniteStateMachine(threading.Thread):
	def __init__(self, server, idxNameSpace, folder, scale):
		threading.Thread.__init__(self)

		self.server = server
		self.idx = idxNameSpace
		self.addressSpace = server.iserver.aspace
		self.nodeManagmentService = NodeManagementService(self.addressSpace)

		self.scale = scale
		self.folder = folder

		self.weight = self.scale.get_child(["%d:WeightSensor"%self.idx,"%d:Weight"%self.idx])
		self.weightBatch = self.scale.get_child(["%d:WeightBatch"%self.idx])
		self.weightAcumulated = self.scale.get_child(["%d:WeightAcumulated" % self.idx])
		self.methodToExecute = self.scale.get_child(["%d:MethodToExecute" % self.idx])

		#################################
		# Maquina de Estados principal
		#################################
		self.simulation = self.scale.get_child(["%d:Program"%idxNameSpace])
		self.create_variables_to_state_and_method(self.simulation,"state")
		self.stateCurrent = self.simulation.get_child(["CurrentState"])
		self.stateCurrentId = self.stateCurrent.get_child(["Id"])
		#################################
		# SubMaquinaEstado
		#################################
		self.subStateMachine = self.stateRunning.get_child(["%d:SubStateMachine" % idxNameSpace])
		self.create_variables_to_state_and_method(self.subStateMachine,"subState")
		self.subStateCurrent = self.subStateMachine.get_child(["CurrentState"])
		self.subStateCurrentId = self.subStateCurrent.get_child(["Id"])

		#Se crearan las referencias que no lograron ser agregadas por medio del modelador
		#debido a que no cuenta con esa opcion
		Utils.generate_node_set(self)

		#se inicializa la maquina de estados principal al estado Ready
		self.simulation.call_method(self.methodCreate.nodeid)

		#Cerrar compuerta de tolva de carga
		#Cerrar compuerta de tolva pesaje


	def run(self):
		while(True):
			if self.stateCurrentId.get_value() == self.stateRunning.nodeid:
				if self.subStateCurrentId.get_value() == self.subStateFilling.nodeid:
					self.Filling()
				elif self.subStateCurrentId.get_value() == self.subStateDumping.nodeid:
					self.Dumping()

			time.sleep(1)


	@uamethod
	def Create(self,parent):
		Utils.changeState(self.stateCurrent,self.stateReady)

	@uamethod
	def Start(self,parent):
		Utils.generate_method(self,parent, "Start")

		Utils.changeState(self.subStateCurrent,self.subStateFilling)
		self.subStateMachine.call_method(self.methodFill.nodeid)

	@uamethod
	def Reset(self,parent):
		Utils.generate_method(self,parent, "Reset")

	@uamethod
	def Resume(self,parent):
		Utils.generate_method(self,parent, "Resume")

	@uamethod
	def Suspend(self,parent):
		Utils.generate_method(self,parent, "Suspend")

	@uamethod
	def Halt(self,parent):
		Utils.generate_method(self,parent, "Halt")

	###################################
	#Metodos para subestados
	####################################
	@uamethod
	def Fill(self,parent):
		Utils.generate_method(self,parent, "%d:Fill"%self.idx)

	@uamethod
	def Dump(self,parent):
		Utils.generate_method(self,parent, "%d:Dump"%self.idx)

	###################################
	#Estados
	###################################
	def Filling(self):
		weightVar = self.weight.get_value()
		weightBatchVar = self.weightBatch.get_value()
		weightAcumulatedVar = self.weightAcumulated.get_value()
		#Abrir compuerta de tolva de carga

		if(weightVar < weightBatchVar):
			print("Scale: "+self.scale.get_browse_name().Name+" -> Filling")
			weightVarTmp = 10.0#round(random.uniform(1.0, 5.0), 0)
			self.weight.set_value(weightVar + weightVarTmp)
		else:
			#Cerrar compuerta de tolva de carga

			weightAcumulatedVar += weightVar
			self.weightAcumulated.set_value(weightAcumulatedVar)
			# Se cambia al estado Dumping
			self.subStateMachine.call_method(self.methodDump.nodeid)

	def Dumping(self):
		weightVar = self.weight.get_value()
		#Abrir compuerta de tolva pesadora

		if(weightVar > 0.0):
			print("Scale: "+self.scale.get_browse_name().Name+" -> Dumping")
			weightVarTmp = 20.0
			self.weight.set_value(weightVar - weightVarTmp)
		else:
			# Cerrar compuerta de tolva pesadora

			# Se cambia al estado Filling
			self.subStateMachine.call_method(self.methodFill.nodeid)

	def create_variables_to_state_and_method(self, node, prefixState):
		# Estados de la maquina de estado principal
		for state in Utils.find_nodes_by_types(node, self.server.get_node(ua.ObjectIds.StateType)):
			# Se crea la variable con el nombre de cada estado
			exec("self." + prefixState + state.get_browse_name().Name + " = " + "state")

		# Metodos de la maquina de estado principal
		for method in node.get_methods():
			# Se crea la variable con el nombre de cada metodo
			exec("self.method" + method.get_browse_name().Name + " = " + "method")
			# Se enlaza el metodo de opc ua con su implentacion
			exec(
				"self.server.link_method(self.method" + method.get_browse_name().Name + ", " + " self." + method.get_browse_name().Name + ")")


#Referencias
#http://mundogeek.net/archivos/2008/04/18/threads-en-python/