# app/utils/psalm_number_converter.py
class PsalmNumberConverter:
    """Convert between Vulgate/Latin and Protestant Psalm numbering"""
    
    @staticmethod
    def to_protestant(vulgate_number):
        """
        Convert Vulgate/Latin Psalm number to Protestant numbering
        Used when querying Augustine's expositions (New Advent uses Protestant)
        """
        if not isinstance(vulgate_number, int) or vulgate_number < 1 or vulgate_number > 150:
            return vulgate_number
            
        # Psalms 1-8 are the same
        if vulgate_number <= 8:
            return vulgate_number
        
        # Psalms 9-147 in Vulgate = Psalms 10-148 in Protestant  
        # Psalms 148-150 are the same
        if vulgate_number <= 147:
            return vulgate_number + 1
        else:
            return vulgate_number
    
    @staticmethod  
    def to_vulgate(protestant_number):
        """
        Convert Protestant Psalm number to Vulgate numbering
        Used when displaying Augustine results to users
        """
        if not isinstance(protestant_number, int) or protestant_number < 1 or protestant_number > 150:
            return protestant_number
            
        # Psalms 1-9 are the same
        if protestant_number <= 9:
            return protestant_number
        
        # Psalms 10-148 in Protestant = Psalms 9-147 in Vulgate
        # Psalms 149-150 are the same  
        if protestant_number <= 148:
            return protestant_number - 1
        else:
            return protestant_number 
            
           