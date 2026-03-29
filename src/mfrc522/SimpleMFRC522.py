from . import BasicMFRC522
from time import sleep


class SimpleMFRC522:
    """
    A class for reading and writing data using the MFRC522 RFID module.

    Attributes:
        MFRC522 (module): The MFRC522 module used for communication with the RFID reader.
        KEY (list): The default authentication key used for reading and writing data.
        TRAILER_BLOCK (int): The default trailer block to authenticate.
        BLOCK_ADDRS (list): The list of block addresses used for reading and writing data.
    """

    def __init__(self):
        """
        Initializes a SimpleMFRC522 instance.
        """
        
        self.KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self.TRAILER_BLOCK = 11
        self.BasicMFRC522 = BasicMFRC522()
        self.MFRC522 = self.BasicMFRC522.MFRC522
        
    def close(self):
        """ 
        Close the MFRC522 instance to free up resources.
        """
        self.BasicMFRC522.close()
    
    def read(self):
        """
        Reads data from the RFID tag.

        Returns:
            tuple: A tuple containing the tag ID (as an integer) and the data read (as a string).
        """
        id, text = self.BasicMFRC522.read_no_block(self.TRAILER_BLOCK)
        while not id:
            sleep(0.2)  # Wait 200ms before retrying to reduce CPU usage
            id, text = self.BasicMFRC522.read_no_block(self.TRAILER_BLOCK)
        return id, text

    def read_id(self):
        """
        Reads the tag ID from the RFID tag.

        Returns:
            id (int): The tag ID as an integer.
        """
        id = self.BasicMFRC522.read_id_no_block()
        while not id:
            sleep(0.2)  # Wait 200ms before retrying to reduce CPU usage
            id = self.BasicMFRC522.read_id_no_block()
        return id

    def write(self, text):
        """
        Writes the given text to an RFID tag.

        Args:
            text (str): A string to be written to the RFID tag.

        Returns:
            tuple: A tuple containing the ID of the tag and the text that was written to the tag.
        """

        id, text_in = self.BasicMFRC522.write_no_block(text, self.TRAILER_BLOCK)
        while not id:
            sleep(0.2)  # Wait 200ms before retrying to reduce CPU usage
            id, text_in = self.BasicMFRC522.write_no_block(text, self.TRAILER_BLOCK)
        return id, text_in

    def write_uid(self, uid, sak=0x08, atqa=None, manufacturer_data=None):
        """
        Overwrite the UID of a Magic MIFARE Gen2 card.

        Blocks until a card is present and the write succeeds.
        See BasicMFRC522.write_uid() for parameter details.

        Args:
            uid (list or bytes): Exactly 4 bytes for the new UID.
            sak (int): Select AcKnowledge byte. 0x08 = MIFARE Classic 1K (default).
            atqa (list): 2-byte ATQA value. Defaults to [0x04, 0x00].
            manufacturer_data (list): 8 bytes appended after ATQA. Defaults to zeros.

        Returns:
            tuple: (new_uid_int, written_data) on success.
        """
        return self.BasicMFRC522.write_uid(uid, sak, atqa, manufacturer_data)

    def write_block0(self, data):
        """
        Write raw 16-byte data to block 0 of a Magic MIFARE Gen2 card.

        Blocks until a card is present and the write succeeds.
        See BasicMFRC522.write_block0() for details.

        Args:
            data (bytes or list): Exactly 16 bytes to write to block 0.

        Returns:
            tuple: (uid_bytes, written_data) on success.
        """
        return self.BasicMFRC522.write_block0(data)

