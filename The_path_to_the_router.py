# Скрипт определения аплинкового порта на комутаторе
# и совершающий подьем по комутации до подключения
# в маршрутизатор марки Extreame.

import telnetlib
import time

switch_manufacturer=['SNR','DGS','BD','TL','Vty']
switch_number=0

def connection(ip):
    login=b'boldov'
    password=b'Boldov'
    connect=telnetlib.Telnet(ip,23)
    connect.expect([b'ame:', b'in:', b'er:'], timeout=10)
    connect.write(login+b"\r\n")
    connect.read_until(b':',timeout=10)
    connect.write(password+b'\r\n')
    connect.expect([b'#',b'>'], timeout=10)
    return connect

def delete_empty_elements_list(list_for_delete_empty_elemets):
    list_for_delete_empty_elemets=list_for_delete_empty_elemets.split(' ') # создание списка по разделителю пустой элемент
    list_without_empty_elemets=list(filter(lambda a: a != '',list_for_delete_empty_elemets)) # удаление пустых элементов списка
    return list_without_empty_elemets

def find_mac_default_gateway(connect,switch_manufacturer):
    connect.write(b"\r\n")
    switch_model=connect.expect([b'#',b'>'], timeout=10)
    switch_model=(switch_model[2]).decode('utf-8')
    for i in range (len(switch_manufacturer)):
        if switch_manufacturer[i] in switch_model:
            switch_model=switch_manufacturer[i]
            break
    if i==0:
        connect.write(b'show arp\r\n')
        connect.read_until(b'Age-time(sec)')
        mac_default_gateway= connect.read_very_eager().decode('utf-8')
        mac_default_gateway= delete_empty_elements_list(mac_default_gateway)
        mac_default_gateway=mac_default_gateway[1]

    elif i==1:
        connect.write(b'show arpentry\r\n')
        time.sleep(1)
        connect.read_until(b'Local/Broadcast')
        mac_default_gateway= connect.read_very_eager().decode('utf-8')
        mac_default_gateway= delete_empty_elements_list(mac_default_gateway)
        mac_default_gateway=mac_default_gateway[2]

    elif i==2:
        connect.write(b'enable\r\n')
        connect.read_until(b':',timeout=10)
        connect.write(b'password\r\n')
        connect.expect([b'#',b'>'], timeout=10)
        connect.write(b'show arp\r\n')
        connect.read_until(b'Interface',timeout=10)
        mac_default_gateway=connect.read_very_eager().decode('utf-8')
        mac_default_gateway= delete_empty_elements_list(mac_default_gateway)
        mac_default_gateway=mac_default_gateway[10]

    elif i==3:
        connect.write(b'enable\r\n')
        connect.read_until(b':',timeout=10)
        connect.write(b'password\r\n')
        connect.expect([b'#',b'>'], timeout=10)
        connect.write(b'show arp\r\n')
        connect.read_until(b'Type',timeout=10)
        mac_default_gateway=(connect.read_until(b'DYNAMIC',timeout=10)).decode('utf-8')
        mac_default_gateway= delete_empty_elements_list(mac_default_gateway)
        mac_default_gateway=mac_default_gateway[-2]

    elif i==4:
        connect.write(b'enable\r\n')
        connect.read_until(b':',timeout=10)
        connect.write(b'password\r\n')
        connect.expect([b'#',b'>'], timeout=10)
        connect.write(b'show arp\r\n')
        connect.read_until(b'Interface',timeout=10)
        mac_default_gateway=(connect.read_until(b'dynamic',timeout=10)).decode('utf-8')
        mac_default_gateway= delete_empty_elements_list(mac_default_gateway)
        mac_default_gateway=mac_default_gateway[-2]
    return mac_default_gateway,i

def convert_mac_for_bdcom(mac):
    mac=mac.replace(':','')
    mac=mac[0:4]+'.'+mac[4:8]+'.'+mac[8:12]
    return mac

def find_ip_default_gateway(connect,mac_default_gateway,switch_model):
        i=switch_model
        if i==0:
            #Определение порта с маком шлюза
            connect.write(b'show mac-address-table address '+mac_default_gateway.encode('utf-8')+b'\n')
            time.sleep(1)
            connect.read_until(b'Ethernet')
            port_with_mac_default_gateway=connect.read_very_eager().decode('utf-8')
            index_for_slice=port_with_mac_default_gateway.find('\n')
            port_with_mac_default_gateway=port_with_mac_default_gateway[:index_for_slice]
            #Определение ипа следуюущего коммутатора по lldp
            connect.write(b'show lldp neighbors interface ethernet '+port_with_mac_default_gateway.encode('utf-8')+b'\n')
            time.sleep(1)
            connect.read_until(b'ipv4')
            connect.read_until(b'Management address : ')
            ip_next_hop=(connect.read_until(b'\r\n')).decode('utf-8')
            extreame_flag=connect.expect([b'ExtremeXOS'], timeout=1)
            ip_next_hop=ip_next_hop[:-1]
            print('ип следующего комутатора:',ip_next_hop)
            print('тип ип следующего комутатора:',type(ip_next_hop))
            print('длинна ип следующего комутатора:',len(ip_next_hop))

        elif i==1:
            connect.write(b'show fdb mac_address '+mac_default_gateway.encode('utf-8')+b'\n')
            time.sleep(1)
            connect.read_until(b'Status')
            connect.read_until(mac_default_gateway.encode('utf-8'))
            port_with_mac_default_gateway=connect.read_very_eager().decode('utf-8')
            index_for_slice=port_with_mac_default_gateway.find('  ')
            port_with_mac_default_gateway=port_with_mac_default_gateway[:index_for_slice]
            #Определение ипа следуюущего коммутатора по lldp
            print(port_with_mac_default_gateway.encode('utf-8'),"<---")
            connect.write(b'show lldp remote_ports '+port_with_mac_default_gateway.encode('utf-8')+b' mode detailed\n')
            extreame_flag=(connect.expect([b'ExtremeXOS'], timeout=1))
            print(extreame_flag[0])
            connect.read_until(b'IPv4')
            connect.read_until(b': ')
            ip_next_hop=connect.read_until(b'\n').decode('utf-8')
            ip_next_hop=ip_next_hop[:-1]
            extreame_flag=connect.expect([b'ExtremeXOS'], timeout=3)
            print('ип следующего комутатора:',ip_next_hop)
            print('тип ип следующего комутатора:',type(ip_next_hop))
            print('длинна ип следующего комутатора:',len(ip_next_hop))
            print(extreame_flag)

        elif i==2:
            connect.write(b'enable\r\n')
            connect.read_until(b':',timeout=10)
            connect.write(b'password\r\n')
            connect.expect([b'#',b'>'], timeout=10)
            mac=convert_mac_for_bdcom(mac_default_gateway)
            connect.write(b'show mac address-table '+mac.encode('utf-8')+b'\r\n')
            #connect.expect([b'#',b'>'], timeout=10)
            connect.read_until(b'DYNAMIC')
            time.sleep(1)
            port_with_mac_default_gateway=(connect.read_until(b'\n')).decode('utf-8')
            port_with_mac_default_gateway=delete_empty_elements_list(port_with_mac_default_gateway)[0]
            port_with_mac_default_gateway=port_with_mac_default_gateway[1:]
            connect.write(b'show lldp neighbors interface gigaEthernet '+port_with_mac_default_gateway.encode('utf-8')+b'\r\n')
            connect.read_until(b'IP:',timeout=1)
            ip_next_hop=(connect.read_until(b'\r\n',timeout=10)).decode('utf-8')
            ip_next_hop=ip_next_hop.split()
            extreame_flag=connect.expect([b'ExtremeXOS'], timeout=1)
            print('ип следующего комутатора:',ip_next_hop)
            print('тип ип следующего комутатора:',type(ip_next_hop))
            print('длинна ип следующего комутатора:',len(ip_next_hop))

        elif i==3:
            connect.write(b'enable\r\n')
            connect.read_until(b':',timeout=10)
            connect.write(b'password\r\n')
            connect.expect([b'#',b'>'], timeout=10)
            connect.write(b'show arp\r\n')
            connect.read_until(b'Type',timeout=10)
            mac_default_gateway=(connect.read_until(b'DYNAMIC',timeout=10)).decode('utf-8')
            mac_default_gateway = delete_empty_elements_list(mac_default_gateway)
            mac_default_gateway=mac_default_gateway[-2]
            connect.write(b'show mac address-table address '+mac_default_gateway.encode('utf-8')+b'\r\n')
            connect.read_until(b'Gi',timeout=10)
            port_with_mac_default_gateway=connect.read_until(b' ',timeout=10)
            connect.write(b'show lldp neighbor-information interface gigabitEthernet '+port_with_mac_default_gateway+b'\r\n')
            time.sleep(1)
            connect.read_until(b'Management address:',timeout=10)
            ip_next_hop=(connect.read_until(b'\r\n',timeout=10)).decode('utf-8')
            ip_next_hop=ip_next_hop.split()
            extreame_flag=connect.expect([b'ExtremeXOS'], timeout=1)
            print('ип следующего комутатора:',ip_next_hop)
            print('тип ип следующего комутатора:',type(ip_next_hop))
            print('длинна ип следующего комутатора:',len(ip_next_hop))

        elif i==4:
            connect.write(b'enable\r\n')
            connect.read_until(b':',timeout=10)
            connect.write(b'password\r\n')
            connect.expect([b'#',b'>'], timeout=10)
            connect.write(b'show mac-address-table addres '+mac_default_gateway.encode('utf-8')+b'\r\n')
            connect.read_until(b'Eth')
            port_with_mac_default_gateway=connect.read_until(b'Learned')
            port_with_mac_default_gateway=port_with_mac_default_gateway.decode('utf-8')
            port_with_mac_default_gateway=port_with_mac_default_gateway.split()
            port_with_mac_default_gateway=port_with_mac_default_gateway[0]
            connect.write(b'show lldp info remote-device detail ethernet '+port_with_mac_default_gateway.encode('utf-8')+b'\r\n')
            extreame_flag=connect.expect([b'ExtremeXOS'], timeout=1)
            connect.read_until(b' Remote Management Address :',timeout=10)
            ip_next_hop=(connect.read_until(b'(IPv4)',timeout=10)).decode('utf-8')
            ip_next_hop=ip_next_hop.split()
            ip_next_hop=ip_next_hop[0]
            print('ип следующего комутатора:',ip_next_hop)
            print('тип ип следующего комутатора:',type(ip_next_hop))
            print('длинна ип следующего комутатора:',len(ip_next_hop))

        return ip_next_hop,extreame_flag[0],i
j=1
extreame_flag=-1
ip_next_hop='10.50.0.1'
print('ип 1го комутатора:',ip_next_hop)
print('тип ип 1го комутатора:',type(ip_next_hop))
print('длинна ип 1го комутатора:',len(ip_next_hop))
while extreame_flag!=0:
#    input('ввдете Enter что бы продолжить')
    print('***************************************')
    print('коммутотор №',j)
    print(ip_next_hop,'***')
    connect=connection(ip_next_hop)
    mac_default_gateway,switch_model=find_mac_default_gateway(connect,switch_manufacturer)
    #print(mac_default_gateway)
    #print(switch_model)
    ip_next_hop,extreame_flag,i=find_ip_default_gateway(connect,mac_default_gateway,switch_model)
    print('вы вошли в ',i,' ветку')
    print('флаг экстрима:',extreame_flag)
    j=j+1
print('Вы поднялись до экстрима')
