#!/usr/bin/python

from binman import *
from multiframe import stripFillingBin
from libdeka import mylog as l
from fcs import Fcs_bitstring
import time
import sys

def parsesds_safe(in_bitstream, in_ch, in_ts, in_mf, cur, db_commit):
    try:
        parsesds(in_bitstream, in_ch, in_ts, in_mf, cur, db_commit)
    except:
        print "SDS Parser failed, bitstream corrupted or unsupported", sys.exc_info()

def parsesds(in_bitstream, in_ch, in_ts, in_mf, cur, db_commit):
    global dsds_data_user_data, dsds_data_user_data, mac_address
    fcs_start_idx = 0
    fcs_end_idx = 0
    fcs_extracted = None
    has_fcs = False
    l("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", "SDS")

    sqll = [None] * 38

    sqll[0] = time.time()
    sqll[1] = in_ch
    sqll[2] = in_ts

    raw = hexFromBites(in_bitstream)
    sqll[4] = raw

    l("RAW> " + raw, "SDS")

    mac_bitstream = in_bitstream
    mac_idx = 0

    # MAC-ACCESS (SCH/HU)
    if in_ts == 0:
        mac_pdu_type = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
        mac_idx += 1

        mac_fill_bit_indication = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
        mac_idx += 2

    # MAC-RESOURCE/MAC-DATA
    else:
        mac_pdu_type = int(mac_bitstream[mac_idx:mac_idx + 2], 2)
        mac_idx += 2
    
        mac_fill_bit_indication = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
        mac_idx = mac_idx + 1 + 4

    # table 21.4.1 MAC PDU types
    if mac_pdu_type == 0:
        mac_length_indication = 0
        # MAC-ACCESS (SCH/HU)
        if in_ts == 0:
            mac_address_type = int(mac_bitstream[mac_idx:mac_idx + 2], 2)
            mac_idx += 2
            if mac_address_type == 0:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 24], 2)
                mac_idx += 24
            if mac_address_type == 1:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 10], 2)
                mac_idx += 10
            if mac_address_type == 2:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 24], 2)
                mac_idx += 24
            if mac_address_type == 3:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 24], 2)
                mac_idx += 24

            opt_flag = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
            mac_idx += 1
            if opt_flag == 1:
                cap_req = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
                mac_idx += 1
                if cap_req == 0:
                    mac_length_indication = int(mac_bitstream[mac_idx:mac_idx + 5], 2)
                    mac_idx += 5
                elif cap_req == 1:
                    frag_flag = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
                    mac_idx += 1
                    res_req = int(mac_bitstream[mac_idx:mac_idx + 4], 2)
                    mac_idx += 4
                    mac_length_indication = 63
                    l("MAC_PDU_FRAGMENTATION_FLAG: " + str(frag_flag), "SDS")
                    l("MAC_PDU_RESERVATION_REQUIREMENT: " + str(res_req), "SDS")
        # MAC-RESOURCE/MAC-DATA
        else:
            mac_length_indication = int(mac_bitstream[mac_idx:mac_idx + 6], 2)
            mac_idx += 6
            mac_address_type = int(mac_bitstream[mac_idx:mac_idx + 3], 2)
            mac_idx += 3
            if mac_address_type == 1:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 24], 2)
                mac_idx += 24
            elif mac_address_type == 2:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 10], 2)
                mac_idx += 10
            elif mac_address_type == 3:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 24], 2)
                mac_idx += 24
            elif mac_address_type == 4:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 24], 2)
                mac_idx += 24
            elif mac_address_type == 5:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 34], 2)
                mac_idx += 34
            elif mac_address_type == 6:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 30], 2)
                mac_idx += 30
            elif mac_address_type == 7:
                mac_address = int(mac_bitstream[mac_idx:mac_idx + 34], 2)
                mac_idx += 34
    
            mac_power_control_flag = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
            mac_idx += 1
    
            if mac_power_control_flag == 1:
                mac_idx += 4
            else:
                pass
    
            mac_slot_granting_flag = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
            mac_idx += 1
    
            if mac_slot_granting_flag == 1:
                mac_idx += 8
            else:
                pass
    
            mac_channel_allocation_flag = int(mac_bitstream[mac_idx:mac_idx + 1], 2)
            mac_idx += 1
    
            sqll[5] = mac_channel_allocation_flag
            l("MAC_PDU_CHANNEL_ALLOCATION_FLAG: " + str(mac_channel_allocation_flag), "SDS")
    
            if mac_channel_allocation_flag == 1:
                # CHANNEL ALLOCATION INFORMATION ELEMENT NOT IMPLEMENTED NOW, ONLY SHIFTING
                mac_idx += 22
    
                if int(mac_bitstream[mac_idx:mac_idx + 1], 2) == 1:
                    mac_idx = mac_idx + 1 + 10
                else:
                    mac_idx += 1
    
                if int(mac_bitstream[mac_idx:mac_idx + 2], 2) == 0:
                    mac_idx = mac_idx + 2 + 2
                else:
                    mac_idx += 2

        sqll[6] = mac_pdu_type
        sqll[7] = mac_fill_bit_indication
        sqll[8] = mac_address

        l("MAC_PDU_TYPE: " + str(mac_pdu_type), "SDS")
        l("MAC_FILL_BIT_INDICATION: " + str(mac_fill_bit_indication), "SDS")
        l("MAC_PDU_LENGTH: " + str(mac_length_indication), "SDS")
        if in_ts == 0:
            addr_type = "FROM"
        else:
            addr_type = "TO"
        l("MAC_PDU_ADDRESS: " + str(mac_address) + " (" + addr_type + ")", "SDS")

        if 34 >= mac_length_indication >= 4:
            tmsdu_length = (mac_length_indication * 8) - mac_idx
            tmsdu_bitstream = mac_bitstream[mac_idx:mac_idx + tmsdu_length]
            l("TM-SDU LENGTH: " + str(tmsdu_length) + " bits", "SDS")
            l("TM-SDU REAL LENGTH: " + str(len(tmsdu_bitstream)), "SDS")
            if tmsdu_length != len(tmsdu_bitstream):
                l("Err: INVALID TM-SDU SIZE (INCOMPLETE TM-SDU)", "SDS")
            if mac_fill_bit_indication == 1:
                tmsdu_bitstream = stripFillingBin(tmsdu_bitstream)
        elif mac_length_indication == 63:
            l("FRAGMENTED TM-SDU", "SDS")
            tmsdu_bitstream = mac_bitstream[mac_idx:]
            tmsdu_length = len(tmsdu_bitstream)
            l("TM-SDU LENGTH: " + str(tmsdu_length) + "bits", "SDS")
        else:
            l("Err: PARSER_RETURN_WRONG_PDU_SIZE: " + str(mac_length_indication), "SDS")
            return

        # START TM-SDU SECTION
        tmsdu_idx = 0

        llc_pdu_type = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 4], 2)
        tmsdu_idx += 4

        if llc_pdu_type not in [0,1,2,3,4,5,6,7]:
            l("Err: PARSER_RETURN_WRONG_LLC_PDU_TYPE: " + str(llc_pdu_type), "SDS")
            return

        if llc_pdu_type in [4,5,6,7]:
            has_fcs = True

        sqll[10] = llc_pdu_type
        l("LLC_PDU_TYPE: " + str(llc_pdu_type), "SDS")

        if llc_pdu_type in [1,3,5,7]:
            tmsdu_idx += 1

        if llc_pdu_type in [0,4]:
            tmsdu_idx += 2

        fcs_start_idx = mac_idx + tmsdu_idx
        # START TL-SDU SECTION

        mle_protocol_discriminator = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 3], 2)
        tmsdu_idx += 3

        sqll[11] = mle_protocol_discriminator
        l("MLE_PROTOCOL_DISCRIMINATOR: " + str(mle_protocol_discriminator), "SDS")
        # See table 18.33: Protocol discriminator information element

        if mle_protocol_discriminator != 2:
            l("Err: PARSER_RETURN_WRONG_MLE_PROTOCOL_DISCIMINATOR: " + str(mle_protocol_discriminator), "SDS")
            return

        # See Table 14.66: PDU type information element contents for CMCE PDU Type
        cmce_pdu_type = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 5], 2)
        tmsdu_idx += 5

        sqll[12] = cmce_pdu_type
        l("CMCE_PDU_TYPE: " + str(cmce_pdu_type), "SDS")

        if cmce_pdu_type != 15:
            l("Err: PARSER_RETURN_WRONG_CMCE_PDU_TYPE: " + str(cmce_pdu_type), "SDS")
            return

        # Skip Area selection on U-SDS-DATA
        if in_ts == 0:
            tmsdu_idx += 4

        dsds_data_calling_party_type_identifier = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 2], 2)
        tmsdu_idx += 2

        sqll[13] = dsds_data_calling_party_type_identifier
        l("DSDS_DATA_PDU_Calling_party_type_identifier: " + str(dsds_data_calling_party_type_identifier), "SDS")

        # Guess CPTI==3 is the same as 1 on some networks
        # see Table 14.43: Calling party type identifier information element contents
        if dsds_data_calling_party_type_identifier in [1,3]:
            dsds_data_address_ssi = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 24], 2)
            tmsdu_idx += 24
            dsds_data_address_extension = None
        elif dsds_data_calling_party_type_identifier == 2:
            dsds_data_address_ssi = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 24], 2)
            tmsdu_idx += 24
            dsds_data_address_extension = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 24], 2)
            tmsdu_idx += 24
        elif dsds_data_calling_party_type_identifier == 0 and in_ts == 0:
            dsds_data_address_ssi = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 8], 2)
            tmsdu_idx += 8
            dsds_data_address_extension = None
        else:
            l("Err: PARSER_RETURN_WRONG_DSDS_DATA_CALLING_PARTY_TYPE_IDENTIFIER: " + str(
                dsds_data_calling_party_type_identifier), "SDS")
            return

        sqll[14] = dsds_data_address_ssi
        sqll[15] = dsds_data_address_extension
        if in_ts == 0:
            addr_type = "TO"
        else:
            addr_type = "FROM"
        l("DSDS_DATA_PDU_ADDRESS_SSI: " + str(dsds_data_address_ssi) + " (" + addr_type + ")", "SDS")
        l("DSDS_DATA_PDU_ADDRESS_EXTENSION: " + str(dsds_data_address_extension), "SDS")

        dsds_data_short_data_type_identifier = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 2], 2)
        tmsdu_idx += 2

        sqll[16] = dsds_data_short_data_type_identifier
        l("DSDS_DATA_PDU_SHORT_DATA_TYPE: " + str(dsds_data_short_data_type_identifier), "SDS")

        dsds_data_length_indicator = 0
        if dsds_data_short_data_type_identifier == 0:
            dsds_data_user_data = tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 16]
            tmsdu_idx += 16
        if dsds_data_short_data_type_identifier == 1:
            dsds_data_user_data = tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 32]
            tmsdu_idx += 32
        if dsds_data_short_data_type_identifier == 2:
            dsds_data_user_data = tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 64]
            tmsdu_idx += 64
        if dsds_data_short_data_type_identifier == 3:
            dsds_data_length_indicator = int(tmsdu_bitstream[tmsdu_idx:tmsdu_idx + 11], 2)
            tmsdu_idx += 11
            l("DSDS_DATA_USER_LENGTH_INDICATOR: " + str(dsds_data_length_indicator), "SDS")
            dsds_data_user_data = tmsdu_bitstream[tmsdu_idx:tmsdu_idx + dsds_data_length_indicator]
            if len(dsds_data_user_data) < dsds_data_length_indicator:
                l("Err: INVALID D-SDS USER DATA SIZE (INCOMPLETE): " + str(dsds_data_length_indicator) + " / " + str(
                    len(dsds_data_user_data)), "SDS")
            l("Debug: D-SDS-DATA BY LEN INDICATOR: " + strFromBites(dsds_data_user_data), "SDS")

        hexa = hexFromBites(dsds_data_user_data)
        asc = strFromBites(dsds_data_user_data)
        sqll[17] = hexa
        sqll[18] = asc
        l("Debug: D-SDS-DATA RAW: " + asc, "SDS")
        l("Debug: D-SDS-DATA RAW: " + hexa, "SDS")

        #if dsds_data_short_data_type_identifier == 0 or dsds_data_short_data_type_identifier == 1 or dsds_data_short_data_type_identifier == 2:
        #    return

        fcs_end_idx = (mac_idx + tmsdu_idx + len(dsds_data_user_data))
        if has_fcs:
            llc_fcs = in_bitstream[fcs_end_idx+1:fcs_end_idx+33]
            fcs_extracted = llc_fcs
            llc_fcs_hex = hex(int(llc_fcs,2))
            tmsdu_bitstream = tmsdu_bitstream[:-32]
            sqll[9] = llc_fcs
            l("LLC_FCS: " + str(llc_fcs), "SDS")
            l("LLC_FCS(hex):" + str(llc_fcs_hex), "SDS")

        if len(in_bitstream) > fcs_end_idx+33:
            l("WARN: REMAINING DATA: " + str(in_bitstream[fcs_end_idx+33:]), "SDS")
        # START OF SDS-TL SECTION

        sdst4_idx = 0
        sdst4_bitstream = dsds_data_user_data

        sdst4_protocol_identifier = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 8], 2)
        sdst4_idx += 8

        sqll[19] = sdst4_protocol_identifier
        l("SDS_TYPE_4_PROTOCOL_INDENTIFIER: " + str(sdst4_protocol_identifier), "SDS")

        # Table 29.21: Protocol identifier information element contents
        if 139 <= sdst4_protocol_identifier <= 255 or 128 <= sdst4_protocol_identifier <= 137:
            l("SDS-TL MESSAGE", "SDS")
            sdst4_message_type = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 4], 2)
            sdst4_idx += 4
            sqll[20] = sdst4_message_type
            l("SDS_TYPE_4_MESSAGE_TYPE: " + str(sdst4_message_type), "SDS")
            if sdst4_message_type == 0:
                sdst4_transfer_delivery_report_request = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 2], 2)
                sdst4_idx += 2
                sdst4_transfer_service_selection = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 1], 2)
                sdst4_idx += 1
                sdst4_transfer_storage = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 1], 2)
                sdst4_idx += 1
                sdst4_transfer_message_reference = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 8], 2)
                sdst4_idx += 8

                if sdst4_transfer_storage == 1:  # NOT FULL IMPLEMENTED NOW, ONLY SHIFTING
                    sdst4_idx += 5
                    forward_address_type = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 3], 2)
                    sqll[21] = forward_address_type
                    l("SDS T4 TRANSFER FORWARD ADDRESS TYPE: " + str(forward_address_type), "SDS")
                    sdst4_idx += 3
                    if forward_address_type == 0:
                        sdst4_idx += 8
                    elif forward_address_type == 1:
                        sdst4_idx += 24
                    elif forward_address_type == 2:
                        sdst4_idx += 48
                    elif forward_address_type == 3:
                        number_of_digits = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 8], 2)
                        sdst4_idx = sdst4_idx + 8 + (number_of_digits * 4)
                        if number_of_digits % 2 == 1:
                            sdst4_idx += 4

                # Text Messaging, see table 29.21
                if sdst4_protocol_identifier == 130:
                    text_message_timestamp_used = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 1], 2)
                    sdst4_idx += 1
                    text_message_coding_scheme = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 7], 2)
                    sdst4_idx += 7
                    if text_message_timestamp_used == 1:
                        text_message_timestamp = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 24], 2)
                        sdst4_idx += 24
                    else:
                        text_message_timestamp = None
                else:
                    text_message_timestamp_used = 0
                    text_message_coding_scheme = 0
                    text_message_timestamp = None

                sdst4_transfer_user_data = sdst4_bitstream[sdst4_idx:]
                sdst4_transfer_user_data_len = len(sdst4_transfer_user_data)
                user_data_txt = strFromBites(sdst4_transfer_user_data)
                user_data_hex = hexFromBites(sdst4_transfer_user_data)
                user_data_ascidx = ascidxFromBites(sdst4_transfer_user_data)

                sqll[22] = sdst4_transfer_delivery_report_request
                sqll[23] = sdst4_transfer_service_selection
                sqll[24] = sdst4_transfer_storage
                sqll[25] = sdst4_transfer_message_reference
                sqll[26] = text_message_timestamp_used
                sqll[27] = text_message_coding_scheme
                sqll[28] = text_message_timestamp
                sqll[29] = user_data_ascidx

                l("SDS T4 TRANSFER DELIVERY REPORT REQUIRED: " + str(sdst4_transfer_delivery_report_request), "SDS")
                l("SDS T4 TRANSFER SERVICE SELECTION / SHORT FROM REPORT: " + str(sdst4_transfer_service_selection),
                  "SDS")
                l("SDS T4 TRANSFER STORAGE: " + str(sdst4_transfer_storage), "SDS")
                l("SDS T4 TRANSFER MESSAGE REFERENCE: " + str(sdst4_transfer_message_reference), "SDS")

                l("SDS T4 TRANSFER TEXT MESSAGE TIMESTAMP USED: " + str(text_message_timestamp_used), "SDS")
                l("SDS T4 TRANSFER TEXT MESSAGE TEXT CODING SCHEME: " + str(text_message_coding_scheme), "SDS")
                l("SDS T4 TRANSFER TEXT MESSAGE TIMESTAMP: " + str(text_message_timestamp), "SDS")

                l("SDS T4 TRANSFER USER DATA ASCII INDEX: " + str(user_data_ascidx), "SDS")
                l("SDS T4 TRANSFER USER DATA LEN: " + str(sdst4_transfer_user_data_len), "SDS")
                l("SDS T4 TRANSFER USER DATA TXT: " + user_data_txt, "SDS")
                l("SDS T4 TRANSFER USER DATA HEX: " + user_data_hex, "SDS")

                if sdst4_transfer_user_data_len % 8 == 1:
                    l("Err: INVALID SDS T4 USER DATA SIZE (INCOMPLETE): " + str(sdst4_transfer_user_data_len), "SDS")

            elif sdst4_message_type == 1:
                sdst4_report_acknowledgement_required = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 1], 2)
                sdst4_idx += 1
                sdst4_report_reserved_bits = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 2], 2)
                sdst4_idx += 2
                sdst4_report_storage = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 1], 2)
                sdst4_idx += 1
                sdst4_report_delivery_status = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 8], 2)
                sdst4_idx += 8
                sdst4_report_message_reference = int(sdst4_bitstream[sdst4_idx:sdst4_idx + 8], 2)
                sdst4_idx += 8
                sdst4_report_data = sdst4_bitstream[sdst4_idx:]

                sdst4_report_user_data = sdst4_bitstream[sdst4_idx:]
                sdst4_report_user_data_len = len(sdst4_report_user_data)
                user_data_txt = strFromBites(sdst4_report_user_data)
                user_data_hex = hexFromBites(sdst4_report_user_data)
                user_data_ascidx = ascidxFromBites(sdst4_report_user_data)

                sqll[30] = sdst4_report_acknowledgement_required
                sqll[31] = sdst4_report_reserved_bits
                sqll[32] = sdst4_report_storage
                sqll[33] = sdst4_report_delivery_status
                sqll[34] = sdst4_report_message_reference
                sqll[35] = sdst4_report_data
                sqll[36] = user_data_ascidx

                l("SDS T4 REPORT ACK REQUIRED: " + str(sdst4_report_acknowledgement_required), "SDS")
                l("SDS T4 REPORT RESERVED BITS: " + str(sdst4_report_reserved_bits), "SDS")
                l("SDS T4 REPORT STORAGE: " + str(sdst4_report_storage), "SDS")
                l("SDS T4 REPORT DELIVERY STATUS: " + str(sdst4_report_delivery_status), "SDS")
                l("SDS T4 REPORT MESSAGE REFERENCE: " + str(sdst4_report_message_reference), "SDS")
                l("SDS T4 REPORT USER DATA: " + sdst4_report_data, "SDS")

                l("SDS T4 REPORT USER DATA ASCII INDEX: " + str(user_data_ascidx), "SDS")
                l("SDS T4 REPORT USER DATA LEN: " + str(sdst4_report_user_data_len), "SDS")
                l("SDS T4 REPORT USER DATA TXT: " + user_data_txt, "SDS")
                l("SDS T4 REPORT USER DATA HEX: " + user_data_hex, "SDS")

            elif sdst4_message_type == 2:
                sdst4_idx += 4 # Table 29.11: SDS-ACK PDU contents
                l("SDS-ACK", "SDS")
                sdst4_ack_delivery_status = sdst4_bitstream[sdst4_idx:sdst4_idx+8]
                sdst4_idx += 8
                sdst4_ack_message_reference = sdst4_bitstream[sdst4_idx:sdst4_idx+8]
                l("SDS-ACK DELIVERY STATUS" + str(sdst4_ack_delivery_status), "SDS")
                l("SDS-ACK MESSAGE REFERENCE" + str(sdst4_ack_message_reference), "SDS")
            else:
                l("Err: PARSER_RETURN_UNSUPPORTED_SDST4_(SDS-TL)_MESSAGE_TYPE: " + str(sdst4_message_type), "SDS")
                l("Err: see \"Table 29.20: Message type information element contents\" for more info", "SDS")
        else:
            l("MESSAGE IS NOT SDS-TL", "SDS")

        sqll[37] = 2
        if fcs_extracted != None:
            fcs_guess = Fcs_bitstring(in_bitstream[fcs_start_idx:fcs_end_idx])
            if fcs_guess == fcs_extracted:
                l("FCS MATCH", "SDS")
                sqll[37] = 1
            else:
                l("FCS part range: %d:%d" % (fcs_start_idx, fcs_end_idx), "SDS")
                l("FCS guess: " + str(Fcs_bitstring(in_bitstream[fcs_start_idx:fcs_end_idx])), "SDS")
                l("FCS expec: " + fcs_extracted, "SDS")
                sqll[37] = 0
        l("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n", "SDS")

    else:
        l("Err: PARSER_RETURN_WRONG_MAC_PDU_TYPE: " + str(mac_pdu_type), "SDS")

    if db_commit != 0:
        cur.execute('INSERT INTO sds VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                tuple(sqll))
