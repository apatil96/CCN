# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event, dpset
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.topology.api import get_switch, get_link
from collections import defaultdict
from ryu.app.wsgi import ControllerBase
from ryu.topology import event, switches

import logging


#switch List
switches = []

class Graph():
    def __init__(self):
        #Edges for the graph
        self.edges = defaultdict(list)
        #Maintains the weight of the edges
        self.weights = {}

    # Adds edges to the graph
    def addEdge(self, from_node, to_node, weight):
        self.edges[from_node].append(to_node)
        self.edges[to_node].append(from_node)
        self.weights[(from_node, to_node)] = weight
        self.weights[(to_node, from_node)] = weight

#class ExampleSwitch13(app_manager.RyuApp):
class PMSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PMSwitch13, self).__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}
        self.topology_api_app = self
        self.datapath_list=[]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src

        # get the received port number from packet_in message.
        in_port = msg.match['in_port']

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        #if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

		#Dynamic path finding
        #if dst in self.mac_to_port[dpid]:
		#    print(src, dst, self.mac_to_port[dpid][src], self.mac_to_port[dpid][dst])
		#    print("self to mac port")
		#    print(self.mac_to_port)

        #    p = get_shortest_path(src, dst, self.mac_to_port[dpid][src], self.mac_to_port[dpid][dst])
		#    print p
        #    out_port = p[0]
        #else:
        #   out_port = ofproto.OFPP_FLOOD

        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions,
                                  data=msg.data)
        datapath.send_msg(out)
		
    @set_ev_cls(dpset.EventDP)
    def get_topology_data(self, ev):
	print("Inside dp event to detect addition and deletion of switches")
        global switches
        switch_list = get_switch(self.topology_api_app, None)
        switches=[switch.dp.id for switch in switch_list]
        self.datapath_list=[switch.dp for switch in switch_list]
        #print "self.datapath_list=", self.datapath_list
        print "switches=", switches
        links_list = get_link(self.topology_api_app, None)
        mylinks=[(link.src.dpid,link.dst.dpid,link.src.port_no,link.dst.port_no) for link in links_list]
        for s1,s2,port1,port2 in mylinks:
          adjacency[s1][s2]=port1
          adjacency[s2][s1]=port2
          #print s1,s2,port1,port2


    #Function to find the shortest path between two nodes
    def get_shortest_path_util(self,graph, initial, end):
        #List to store the shortest path between nodes
        shortestPathList = {initial: (None, 0)}
        #Setting start node as the current node
        currentNode = initial
        #This set stores the visited nodes so we do not revisit the visited nodes and end up in an infite loop
        nodesVisitedSet = set()
        while currentNode != end:
            nodesVisitedSet.add(currentNode)
            destinations = graph.edges[currentNode]

            weightToCurrentNode = shortestPathList[currentNode][1]
            for node in destinations:
                #calculating the total weight uptil a node using the current path
                totalWeight = graph.weights[(currentNode, node)] + weightToCurrentNode
                if node not in shortestPathList:
                    shortestPathList[node] = (currentNode, totalWeight)
                else:
                    currentLeastWeight = shortestPathList[node][1]
                    if currentLeastWeight > totalWeight:
                        # updating shortest path list if the currentleastweight is greater than the total calculated weight upto this node
                        shortestPathList[node] = (currentNode, totalWeight)

            #list of all the possible next adjacent nodes that hasnt been visited
            next_destinations = {node: shortestPathList[node] for node in shortestPathList if node not in nodesVisitedSet}
            #Checking if the next destination is empty which means the node is not reachable
            if not next_destinations:
                return "Route Not Possible"
            #selecting next current node using the minimum value
            currentNode = min(next_destinations, key=lambda k: next_destinations[k][1])

        finalPath = []
        #Creating the final shortest path between the start and end node using the shortestPathList
        while currentNode is not None:
            finalPath.append(currentNode)
            next_node = shortestPathList[currentNode][0]
            currentNode = next_node

        finalPath = finalPath[::-1]
        return finalPath


    def get_shortest_path(self):
        # Running the program with the provided topology
        toplogy = Graph()

        #created list of edges as per the given toplogy
        edges = [
            ('h1', 'X', 0),
            ('h2', 'T', 0),
            ('X', 'Y', 4),
            ('Y', 'V', 2),
            ('V', 'U', 1),
            ('X', 'W', 1),
            ('W', 'U', 3),
            ('U', 'S', 4),
            ('U', 'T', 2),
            ('X', 'V', 3),
            ('Y', 'T', 4),
            ('Y', 'Z', 12),
            ('Z', 'T', 2),
            ('V', 'T', 9),
            ('T', 'S', 1),
            ('V', 'W', 1)
        ]

        #Populating the graph
        for e in edges:
            toplogy.addEdge(*e)

        path = self.get_shortest_path_util(toplogy, 'h1', 'h2')
        logger=logging.getLogger()
        logger.info("Shortest path between host h1 and h2 is")
        logger.info(path[1:-1])

pmswitch=PMSwitch13()
pmswitch.get_shortest_path()

# References:
# https://www.geeksforgeeks.org/dijkstras-shortest-path-algorithm-greedy-algo-7/
# http: // benalexkeen.com / implementing - djikstras - shortest - path - algorithm -with-python /
# https: // www.codingame.com / playgrounds / 1608 / shortest - paths -with-dijkstras - algorithm / dijkstras - algorithm


