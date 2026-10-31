# Cisco Packet Tracer Build Guide

This guide builds a representative campus network separately from the Python dashboard. The Python dashboard demonstrates algorithms; Packet Tracer demonstrates device configuration and connectivity.

## A. Suggested physical/logical devices

- 1 core router (for example, a Cisco 2911 or 1941 model available in your Packet Tracer version)
- 6 department routers: CS, Electronics, Administration, Labs, Library, Server Room
- 6 access switches (one per department)
- At least 1 PC per department; optionally add more PCs
- 1 server connected to the Server Room switch

Device model names and interface availability differ by Packet Tracer version. Use available Ethernet interfaces or serial interfaces as appropriate.

## B. Topology links

Connect the core router to each department router, and add redundant links to demonstrate alternative paths:

- CORE—CS
- CORE—EE
- CORE—ADMIN
- CORE—LAB
- CORE—LIB
- CORE—SERVER
- CS—LAB
- EE—LAB
- ADMIN—LIB
- LAB—SERVER
- LIB—SERVER

Use copper straight-through cables for router-to-switch and PC-to-switch Ethernet links. For router-to-router Ethernet links, Packet Tracer generally supports automatic connection or copper crossover/straight-through depending on model and auto-MDIX behavior. Confirm interface status.

## C. Department LAN addressing

Use these LANs. Set the router interface facing each department switch to the gateway address.

| Department | LAN subnet | Gateway | Example PC |
|---|---|---|---|
| Computer Science | 192.168.10.0/24 | 192.168.10.1 | 192.168.10.10 |
| Electronics | 192.168.20.0/24 | 192.168.20.1 | 192.168.20.10 |
| Administration | 192.168.30.0/24 | 192.168.30.1 | 192.168.30.10 |
| Computer Labs | 192.168.40.0/24 | 192.168.40.1 | 192.168.40.10 |
| Library | 192.168.50.0/24 | 192.168.50.1 | 192.168.50.10 |
| Server Room | 192.168.60.0/24 | 192.168.60.1 | 192.168.60.10 |

Subnet mask for all these LANs: `255.255.255.0`.

Each router-to-router link must use its own separate transit subnet. For example, use a `/30` subnet for each point-to-point link. Do not reuse the department LAN subnets on transit links.

## D. Configure interfaces

On each router, identify the actual interface names using `show ip interface brief`. Example syntax for a router LAN interface:

```text
enable
configure terminal
interface gigabitEthernet 0/0
ip address 192.168.10.1 255.255.255.0
no shutdown
end
show ip interface brief
```

Replace the interface name and IP address for your actual device and department. Configure every router-to-router interface with a unique transit IP address at both ends.

## E. Routing protocol option

For a beginner-friendly working multi-router demo, configure OSPF on all routers after addressing the transit links and LAN interfaces. Example on a router:

```text
enable
configure terminal
router ospf 1
network 192.168.10.0 0.0.0.255 area 0
network <YOUR_TRANSIT_SUBNET> <WILDCARD_MASK> area 0
end
show ip route
show ip ospf neighbor
```

Replace the placeholders with the real transit subnet and wildcard mask. Repeat the correct LAN and transit `network` statements on each router. Ensure the OSPF process includes every relevant interface. Alternatively, use RIP v2 if your instructor specifically asks for a distance-vector protocol and the Packet Tracer router model supports it.

## F. Configure a PC

On the PC, choose **Desktop → IP Configuration**:
- IP address: for example `192.168.10.10`
- Subnet mask: `255.255.255.0`
- Default gateway: `192.168.10.1`

Configure each PC according to its department LAN.

## G. Test

From a PC, open **Desktop → Command Prompt**:
```text
ping 192.168.20.10
```
Use the real IP address of a PC in another department. Also test the server IP. On routers:
```text
show ip route
show ip interface brief
traceroute 192.168.60.10
```
Some Packet Tracer device versions may use `tracert` from a PC.

## H. Link failure demonstration

1. Confirm a cross-department ping succeeds.
2. Record `show ip route` and `traceroute` output.
3. Delete or disable one router-to-router link.
4. Wait for the selected routing protocol to reconverge.
5. Run the ping and route commands again.
6. Explain that redundant links can provide an alternative path if the routing protocol has learned it.

## Important

This is a build plan, not a preconfigured `.pkt` file. Interface names, router models, transit IP addresses, and protocol configuration must match the exact Packet Tracer devices you choose. The browser dashboard and Packet Tracer do not exchange routing updates automatically.
