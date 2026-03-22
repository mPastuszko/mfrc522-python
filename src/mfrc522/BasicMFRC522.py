from . import MFRC522
from time import sleep

class BasicMFRC522:
    """
    A class for reading, writing and clearing data using the MFRC522 RFID module with extended function.

    Attributes:
        MFRC522 (module): The MFRC522 module used for communication with the RFID reader.
        KEY (list): The default authentication key used for reading and writing data.
    """
    def __init__(self, KEY=[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]):
        """
        Initializes a BasicMFRC522 instance.

        Args:
            KEY (list): The authentication key used for reading and writing data.
        """
        self.MFRC522 = MFRC522()  # Create an instance of the MFRC522 class
        self.KEY = KEY  # Set the authentication key

    def close(self):
        """ 
        Close the MFRC522 instance to free up resources.
        """
        self.MFRC522.Close()
        
    def read_sector(self, trailer_block):
        """
        Read data from a sector of the RFID tag.

        Args:
            trailer_block (int): The block number of the sector trailer.

        Returns:
            tuple: A tuple containing the tag ID (as an integer) and the data read (as a string).
        """
        id, text = self.read_no_block(trailer_block)
        while not id:
            sleep(0.2)  # Wait 200ms before retrying to reduce CPU usage
            id, text = self.read_no_block(trailer_block)
        return id, text

    def read_sectors(self, trailer_blocks):
        """
        Read data from multiple sectors of the RFID tag.

        Args:
            trailer_blocks (list): The list of block numbers of the sector trailers.

        Returns:
            tuple: A tuple containing the tag ID (as an integer) and the concatenated data read from all sectors (as a string).
        """
        text_all = ''
        for trailer_block in trailer_blocks:
            id, text = self.read_sector(trailer_block)
            text_all += text
        return id, text_all

    def read_id(self):
        """
        Read the tag ID from the RFID tag.

        Returns:
            int: The tag ID as an integer.
        """
        id = self.read_id_no_block()
        while not id:
            sleep(0.2)  # Wait 200ms before retrying to reduce CPU usage
            id = self.read_id_no_block()
        return id

    def read_id_no_block(self):
        """
        Attempt to read the tag ID from the RFID tag.

        Returns:
            int: The tag ID as an integer, or None if the operation fails.
        """
        # Send request to RFID tag
        (status, TagType) = self.MFRC522.Request(self.MFRC522.PICC_REQIDL)
        if status != self.MFRC522.MI_OK:
            return None

        # Anticollision, return UID if successful
        (status, uid) = self.MFRC522.Anticoll()
        if status != self.MFRC522.MI_OK:
            return None

        # Convert UID to integer and return as the tag ID
        return self._uid_to_num(uid)

    def read_no_block(self, trailer_block):
        """
        Attempt to read data from the RFID tag.

        Args:
            trailer_block (int): The block number of the sector trailer.
            block_addr (tuple): The block numbers of the data blocks to read.

        Returns:
            tuple: A tuple containing the tag ID (as an integer) and the data read (as a string),
                or (None, None) if the operation fails.
        """
        if not self._check_trailer_block(trailer_block):
            raise ValueError("Invalid Trailer Block {trailer_block}")

        block_addr = (trailer_block-3, trailer_block-2, trailer_block-1)

        # Send request to RFID tag
        (status, TagType) = self.MFRC522.Request(self.MFRC522.PICC_REQIDL)
        if status != self.MFRC522.MI_OK:
            return None, None

        # Anticollision, return UID if successful
        (status, uid) = self.MFRC522.Anticoll()
        if status != self.MFRC522.MI_OK:
            return None, None

        # Convert UID to integer and store as the tag ID
        id = self._uid_to_num(uid)

        # Select the RFID tag
        self.MFRC522.SelectTag(uid)

        # Authenticate with the tag using the provided key
        status = self.MFRC522.Authenticate(self.MFRC522.PICC_AUTHENT1A, trailer_block, self.KEY, uid)

        # Initialize variables for storing data and text read from the tag
        data = []
        text_read = ''

        try:
            if status == self.MFRC522.MI_OK:
                # Read data blocks specified by block_addr
                for block_num in block_addr:
                    block = self.MFRC522.ReadTag(block_num)
                    if block:
                        data += block

                # Convert data to string
                if data:
                    text_read = ''.join(chr(i) for i in data)

            # Stop cryptographic communication with the tag
            self.MFRC522.StopCrypto1()

            # Return the tag ID and the read data
            return id, text_read

        except:
            # Stop cryptographic communication with the tag in case of exception
            self.MFRC522.StopCrypto1()

            # Return None, None if an exception occurs
            return None, None
        
    def write_sector(self, text, trailer_block):
        """
        Write data to a sector of the RFID tag.

        Args:
            text (str): The data to write.
            trailer_block (int): The block number of the sector trailer.

        Returns:
            tuple: A tuple containing the tag ID (as an integer) and the data written (as a string).
        """

        # Write the data to the RFID tag using the helper function write_no_block
        id, text_in = self.write_no_block(text, trailer_block)

        # Retry writing if it fails initially
        while not id:
            sleep(0.2)  # Wait 200ms before retrying to reduce CPU usage
            id, text_in = self.write_no_block(text, trailer_block)

        # Return the tag ID and the written data
        return id, text_in

    def write_sectors(self, text, trailer_blocks):
        """
        Write data to multiple sectors of the RFID tag.

        Args:
            text (str): The data to write.
            trailer_blocks (list): The list of block numbers of the sector trailers.

        Returns:
            tuple: A tuple containing the tag ID (as an integer) and the concatenated data written to all sectors (as a string).
        """
        # Split the input text into chunks of 48 characters
        text_formated_list = self._split_string(text)

        # Initialize an empty string to store the concatenated data
        text_all = ''

        # Iterate through the trailer_blocks list
        for i in range(0, len(trailer_blocks)):
            try:
                # Write data to the sector using the write_sector function
                id, text = self.write_sector(text_formated_list[i], trailer_blocks[i])

                # Concatenate the written data to the text_all string
                text_all += text
            except IndexError:
                # Ignore any index errors that may occur if there are fewer chunks than trailer blocks
                pass

        # Return the tag ID and the concatenated data
        return id, text_all

    def write_no_block(self, text, trailer_block):
        """
        Attempt to write data to the RFID tag.

        Args:
            text (str): The data to write.
            trailer_block (int): The block number of the sector trailer.
            block_addr (tuple): The block numbers of the data blocks to write.

        Returns:
            tuple: A tuple containing the tag ID (as an integer) and the data written (as a string), or (None, None) if the operation fails.
        """
        if not self._check_trailer_block(trailer_block):
            raise ValueError("Invalid Trailer Block {trailer_block}")

        block_addr = (trailer_block-3, trailer_block-2, trailer_block-1)
        text = str(text)

        # Send request to RFID tag
        (status, TagType) = self.MFRC522.Request(self.MFRC522.PICC_REQIDL)
        if status != self.MFRC522.MI_OK:
            return None, None

        # Anticollision, return UID if success
        (status, uid) = self.MFRC522.Anticoll()
        if status != self.MFRC522.MI_OK:
            return None, None

        # Convert UID to integer and store as id
        id = self._uid_to_num(uid)

        # Select the RFID tag using the UID
        self.MFRC522.SelectTag(uid)

        # Authenticate with the sector trailer block using the default key
        status = self.MFRC522.Authenticate(self.MFRC522.PICC_AUTHENT1A, trailer_block, self.KEY, uid)

        # Read the sector trailer block
        self.MFRC522.ReadTag(trailer_block)

        try:
            if status == self.MFRC522.MI_OK:
                # Prepare the data to be written
                data = bytearray()
                data.extend(bytearray(text.ljust(len(block_addr) * 16).encode('ascii')))
                i = 0
                for block_num in block_addr:
                    # Write the data to the corresponding data blocks
                    self.MFRC522.WriteTag(block_num, data[(i*16):(i+1)*16])
                    i += 1

            # Stop encryption
            self.MFRC522.StopCrypto1()

            # Return the tag ID and the written data
            return id, text[0:(len(block_addr) * 16)]
        except:
            # Stop encryption and return None if an exception occurs
            self.MFRC522.StopCrypto1()
            return None, None

    def clear_sector(self, trailer_block):
        """
        Clear a sector of the RFID tag by writing zeros to all data blocks.

        Args:
            trailer_block (int): The block number of the sector trailer.

        Returns:
            int: The tag ID as an integer.
        """
        # Clear the sector using the clear_no_sector function
        id = self.clear_no_sector(trailer_block)

        # Retry clearing the sector until it succeeds and returns a tag ID
        while not id:
            sleep(0.2)  # Wait 200ms before retrying to reduce CPU usage
            id = self.clear_no_sector(trailer_block)

        # Return the tag ID
        return id

    def clear_sectors(self, trailer_blocks):
        """
        Clear multiple sectors of the RFID tag by writing zeros to all data blocks.

        Args:
            trailer_blocks (list): The list of block numbers of the sector trailers.

        Returns:
            int: The tag ID as an integer.
        """
        # Iterate through the trailer_blocks list and clear each sector
        for i in trailer_blocks:
            id = self.clear_sector(i)

        # Return the tag ID
        return id

    def clear_no_sector(self, trailer_block):
        """
        Clear a sector of the RFID tag by writing zeros to all data blocks.

        Args:
            trailer_block (int): The block number of the sector trailer.

        Returns:
            int: The tag ID as an integer, or None if the operation fails.
        """
        if not self._check_trailer_block(trailer_block):
            raise ValueError("Invalid Trailer Block {trailer_block}")

        block_addr = (trailer_block-3, trailer_block-2, trailer_block-1)

        # Send request to RFID tag
        (status, TagType) = self.MFRC522.Request(self.MFRC522.PICC_REQIDL)
        if status != self.MFRC522.MI_OK:
            return None

        # Anticollision, return UID if success
        (status, uid) = self.MFRC522.Anticoll()
        if status != self.MFRC522.MI_OK:
            return None

        # Convert UID to integer and store as id
        id = self._uid_to_num(uid)

        # Select the RFID tag using the UID
        self.MFRC522.SelectTag(uid)

        # Authenticate with the sector trailer block using the default key
        status = self.MFRC522.Authenticate(self.MFRC522.PICC_AUTHENT1A, trailer_block, self.KEY, uid)

        # Read the sector trailer block
        self.MFRC522.ReadTag(trailer_block)

        # Determine the block addresses of the data blocks in the sector

        try:
            if status == self.MFRC522.MI_OK:
                # Prepare data with all zeros
                data = [0x00]*16

                # Write zeros to each data block in the sector
                for block_num in block_addr:
                    self.MFRC522.WriteTag(block_num, data)

            # Stop encryption
            self.MFRC522.StopCrypto1()

            # Return the tag ID
            return id
        except:
            # Stop encryption and return None if an exception occurs
            self.MFRC522.StopCrypto1()
            return None

    def write_block0_no_block(self, data):
        """
        Attempt to write raw 16-byte data to block 0 of a Magic MIFARE Gen2 card.

        Block 0 contains the UID, BCC, SAK, ATQA and manufacturer data. This
        method uses MIFARE_OpenUidBackdoor() to unlock the write and will fail
        silently on standard (non-magic) cards.

        Args:
            data (bytes or list): Exactly 16 bytes to write to block 0.

        Returns:
            tuple: (uid_bytes, written_data) on success, (None, None) on failure.
                uid_bytes is the first 4 bytes of the written data (the new UID).
        """
        if len(data) != 16:
            raise ValueError("Block 0 data must be exactly 16 bytes.")

        if not self.MFRC522.MIFARE_OpenUidBackdoor():
            return None, None

        self.MFRC522.WriteTag(0, list(data))
        return list(data[:4]), list(data)

    def write_block0(self, data):
        """
        Write raw 16-byte data to block 0 of a Magic MIFARE Gen2 card, blocking
        until successful.

        See write_block0_no_block() for details.
        """
        uid_bytes, written = self.write_block0_no_block(data)
        while uid_bytes is None:
            uid_bytes, written = self.write_block0_no_block(data)
        return uid_bytes, written

    def write_uid_no_block(self, uid, sak=0x08, atqa=None, manufacturer_data=None):
        """
        Attempt to overwrite the UID of a Magic MIFARE Gen2 card.

        Constructs the full 16-byte manufacturer block from the given UID,
        automatically computing the BCC (XOR of the 4 UID bytes) and using
        sensible defaults for SAK, ATQA and manufacturer bytes.

        Args:
            uid (list or bytes): Exactly 4 bytes for the new UID.
            sak (int): Select AcKnowledge byte. 0x08 = MIFARE Classic 1K (default).
            atqa (list): 2-byte ATQA value. Defaults to [0x04, 0x00].
            manufacturer_data (list): 8 bytes appended after ATQA. Defaults to zeros.

        Returns:
            tuple: (new_uid_int, written_data) on success, (None, None) on failure.
                new_uid_int is the new UID as an integer (for consistency with other
                read/write methods).
        """
        if len(uid) != 4:
            raise ValueError("UID must be exactly 4 bytes.")
        if atqa is None:
            atqa = [0x04, 0x00]
        if manufacturer_data is None:
            manufacturer_data = [0x00] * 8

        bcc = uid[0] ^ uid[1] ^ uid[2] ^ uid[3]
        block0 = list(uid) + [bcc, sak] + list(atqa) + list(manufacturer_data)

        uid_bytes, written = self.write_block0_no_block(block0)
        if uid_bytes is None:
            return None, None

        uid_int = self._uid_to_num(list(uid) + [bcc])
        return uid_int, written

    def write_uid(self, uid, sak=0x08, atqa=None, manufacturer_data=None):
        """
        Overwrite the UID of a Magic MIFARE Gen2 card, blocking until successful.

        See write_uid_no_block() for parameter details.
        """
        uid_int, written = self.write_uid_no_block(uid, sak, atqa, manufacturer_data)
        while uid_int is None:
            uid_int, written = self.write_uid_no_block(uid, sak, atqa, manufacturer_data)
        return uid_int, written

    def _check_trailer_block(self, trailer_block):
        if (trailer_block+1)%4 == 0:
            return True
        else:
            return False

    def _uid_to_num(self, uid):
        """
        Convert the UID (Unique Identifier) of the RFID tag to an integer.

        Args:
            uid (list): The UID as a list of bytes.

        Returns:
            int: The UID as an integer.
        """
        n = 0
        for i in range(0, 5):
            n = n * 256 + uid[i]
        return n

    def _split_string(self, string):
        """
        Split a string into chunks of 48 characters.

        Args:
            string (str): The string to split.

        Returns:
            list: A list of strings, each containing up to 48 characters.
        """
        l = list()
        for i in range(0, len(string), 48):
            l.append(string[i:i+48])

        # If the last chunk is less than 48 characters, pad it with null characters ('\0')
        if len(l[-1]) < 48:
            l[-1] += '\0'*(48-len(l[-1]))

        return l
