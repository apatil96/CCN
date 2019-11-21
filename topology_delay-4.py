from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost,Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
from mininet.link import TCLink

def myNetwork():
    net = Mininet (topo=None,build=False,ipBase='10.0.0.0/8',autoStaticArp=True)
    info('Adding controller \n')
    c0=net.addController('c0',controller=OVSController,port=6633)
    info('Add Siwches \n')
    X= net.addSwitch('s1',stp='true')
    Y= net.addSwitch('s2',stp='true')
    V= net.addSwitch('s3',stp='true')
    W= net.addSwitch('s4',stp='true')
    Z= net.addSwitch('s5',stp='true')
    U= net.addSwitch('s6',stp='true')
    T= net.addSwitch('s7',stp='true')
    S= net.addSwitch('s8',stp='true')
    info('Add hosts \n')
    h1=net.addHost('h1',ip='10.0.0.1/24')
    h2=net.addHost('h2',ip='10.0.0.2/24')

    info ('Add Links')
    net.addLink(h1,X)
    net.addLink(h2,T)
#==========================
    net.addLink(X,Y,cls=TCLink,delay='4ms')
    net.addLink(X,W,cls=TCLink, delay='1ms')
    net.addLink(X,V,cls=TCLink, delay='3ms')
    net.addLink(Y,V,cls=TCLink, delay='2ms')
    net.addLink(Y,Z,cls=TCLink, delay='12ms')
    net.addLink(Y,T,cls=TCLink, delay='4ms')
    net.addLink(V,T,cls=TCLink, delay='9ms')
    net.addLink(V,U,cls=TCLink, delay='1ms')
    net.addLink(W,V,cls=TCLink, delay='1ms')
    net.addLink(W,U,cls=TCLink, delay='3ms')
    net.addLink(Z,T,cls=TCLink, delay='2ms')
    net.addLink(U,T,cls=TCLink, delay='2ms')
    net.addLink(U,S,cls=TCLink, delay='4ms')
    net.addLink(T,S,cls=TCLink, delay='1ms')
#===========================
    info('Starting Network')
    net.build()
    info('Starting controllers \n')
    for controller in net.controllers:
    	controller.start()
    info('starting switches \n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s4').start([c0])
    net.get('s5').start([c0])
    net.get('s6').start([c0])
    net.get('s7').start([c0])
    net.get('s8').start([c0])

    info('Post configure switches and hosts \n')
    CLI(net)
    net.stop()


if __name__== '__main__':
    setLogLevel('info')
    topo=myNetwork()
