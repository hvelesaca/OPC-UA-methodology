import os.path
import Scale
import Utils
from opcua import Server

try:
	from IPython import embed
except ImportError:
	import code

	def embed():
		vars = globals()
		vars.update(locals())
		shell = code.InteractiveConsole(vars)
		shell.interact()

if __name__ == '__main__':
	scriptDir = os.path.dirname(__file__)
	endpoint = "opc.tcp://0.0.0.0:4840/UA/Server/Scale"
	#Server name
	serverName = "OpcUa Server Scale"
	#Path of the XML file containing the server model
	model_filepath = os.path.join(scriptDir, "node_set.xml")
	uri = "http://examples.freeopcua.github.io"

	server = Server()
    #Load certificates and private keys from the server. Enable endpoints with signing and encryption.
	server.load_certificate("certificate.der")
	server.load_private_key("private-key.pem")
	#The model is imported from an XML
	server.import_xml(model_filepath)
	server.set_endpoint(endpoint)
	#Name is assigned to the server
	server.set_server_name(serverName)
    #The namespace index is obtained according to the indicated name
	idx = server.get_namespace_index("urn:tfm:python:server")
	folder = server.get_node("ns=%d;i=2084"%idx)
	scaleType = server.get_node("ns=%d;i=2168"%idx)

	listStateMachine = []
	for scale in Utils.find_nodes_by_types(folder, scaleType):
		listStateMachine.append(Scale.ProgramFiniteStateMachine(server, idx, folder, scale))

    #Server starts
	server.start()
	server.export_xml_by_ns(path="node_set_export.xml")

	try:
        #Start all state machines that appear on the server
		for stateMachine in listStateMachine:
			stateMachine.start()

			# enable following if you want to subscribe to nodes on server side
			handler = Scale.HandlerStateMachine(stateMachine)
			subscription = server.create_subscription(1000, handler)
			handle = subscription.subscribe_data_change(stateMachine.methodToExecute)
		embed()
	finally:
		server.stop()

