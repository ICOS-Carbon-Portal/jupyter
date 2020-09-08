#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#Create quiz questions:  
q1_prompt = '\n\n1. Which gas has the highest concentration in the Earth\'s atmosphere?'
q2_prompt = '\n\n2. Which gases are greenhouse gases? (3 correct answers)'
q3_prompt = '\n\n3. Which of the following options are CO\u2082 sinks (3 correct answers):'
q4_prompt = '\n\n4. Which of the following options are CO\u2082 sources (4 correct answers):'
q5_prompt = '\n\n5. During what season is the highest concentration of CO\u2082 observed in the Earth\'s northern hemisphere?'
q6_prompt = '\n\n6. Which process is responsible for the lower CO\u2082-concentration in the atmosphere \n   of Earth\'s northern hemisphere during autumn?'
    
#Create a list of options for every question:
q1_options = ['Carbon dioxide (CO\u2082)', 'Oxygen (O\u2082)', 'Nitrogen (N\u2082)', 'Argon (Ar)']
q2_options = ['Nitrous oxide (N\u2082O)', 'Carbon dioxide (CO\u2082)', 'Oxygen (O\u2082)', 'Nitrogen (N\u2082)', 'Methane (CH\u2084)']
q3_options = ['Trees & vegetation', 'Oceanic respiration', 'Reforestation',  'Deforestation', 'Oceanic photosynthesis', 'Plant respiration']
q4_options = ['Forest fires', 'Volcanic eruptions', 'Decaying animal/plant remains',  'Reforestation', 'Burning fossil fuels', 'Manure']
q5_options = ['Spring', 'Summer', 'Autumn', 'Winter']
q6_options = ['Livestock farming', 'Burning fossil fuels', 'Forest fires', 'Photosynthesis']
    
#Create a list of feedbacks per option for every question:
q1_feedback = ['\033[1;93m'+'About 0.04% of the Earth\'s atmosphere consists of carbon dioxide (CO\u2082).'+'\033[1;93m',
               '\033[1;93m'+'About 20.95%'+' of the Earth\'s atmosphere consists of oxygen (O\u2082).'+'\033[1;93m',
               '\033[1;96m'+'Correct!\nAbout 78% of the Earth\'s atmosphere consists of nitrogen (N\u2082). '+'\033[1;96m',
               '\033[1;93m'+'About 0.93% of the Earth\'s atmosphere consists of argon (Ar)'+'\033[1;93m']
    
q2_feedback = ['\033[1;96m'+'Correct! N\u2082O is emitted from e.g. nitrogen-fertilized agricultural land.'+'\033[1;96m',
               '\033[1;96m'+'Correct! CO\u2082 is emitted from e.g. burning fossil fuels.'+'\033[1;96m',
               '\033[1;93m'+'O\u2082 is not a greenhouse gas. Living organisms need O\u2082 to breath.'+'\033[1;93m',
               '\033[1;93m'+'N\u2082 is not a greenhouse gas. N\u2082 is the most common gas in Earth\'s atmosphere.'+'\033[1;93m', 
               '\033[1;96m'+'Correct! CH\u2084 is emitted as a by-product of animal digestion.'+'\033[1;96m']
    
q3_feedback = ['\033[1;96m'+'Correct! Plants take up atmospheric CO\u2082 during photosynthesis.'+'\033[1;96m',
               '\033[1;93m'+'Oceanic respiration releases CO\u2082 from the oceans to the air.'+'\033[1;93m',
               '\033[1;96m'+'Correct! Plants take up atmospheric CO\u2082 during photosynthesis.'+'\033[1;96m',
               '\033[1;93m'+'Less trees lead to a decrease in the uptake of CO\u2082 for photosynthesis.'+'\033[1;93m', 
               '\033[1;96m'+'Correct! Oceanic plants take up CO\u2082 when they photosynthesize.'+'\033[1;96m',
               '\033[1;93m'+'Plants release CO\u2082 during respiration.'+'\033[1;93m']

q4_feedback = ['\033[1;96m'+'Correct! Forest fires release CO\u2082 into the atmosphere.'+'\033[1;96m',
               '\033[1;96m'+'Correct! Volcanic eruptions release CO\u2082 into the atmosphere.'+'\033[1;96m',
               '\033[1;96m'+'Correct! Decaying dead organic matter releases CO\u2082 into the atmosphere.'+'\033[1;96m',
               '\033[1;93m'+'More plants lead to a larger uptake of atmospheric CO\u2082 from photosynthesis.'+'\033[1;93m', 
               '\033[1;96m'+'Correct! The burning fossil fuels releases CO\u2082 into the atmosphere.'+'\033[1;96m',
               '\033[1;93m'+'CH\u2084 & N\u2082O are released from livestock manure.'+'\033[1;93m']

q5_feedback = ['\033[1;96m'+'Correct!\nCO\u2082 is accumulated during winter.\nTherefore, the highest concentration of CO\u2082 is observed in early spring.'+'\033[1;96m',
               '\033[1;93m'+'Photosynthetic activity increases over summer, increasing the uptake of atmospheric CO\u2082.\nAs a result, the total concentration of CO\u2082 in the atmosphere drops.'+'\033[1;93m',
               '\033[1;93m'+'Photosynthetic activity declines during autumn & the uptake of CO\u2082 from plants drops.\nAs a result, CO\u2082 begins to accumulate in the atmosphere.'+'\033[1;93m',
               '\033[1;93m'+'Photosynthetic activity is very low during winter & the uptake of CO\u2082 from plants is low.\nTherefore, the total concentration of CO\u2082 in the atmosphere increases.'+'\033[1;93m']

q6_feedback = ['\033[1;93m'+'Livestock farming is responsible for larger emissions of greenhouse gases.'+'\033[1;93m',
               '\033[1;93m'+'The burning of fossil fuels releases larger quantities of CO\u2082.'+'\033[1;93m',
               '\033[1;93m'+'Forest fires release CO\u2082 to the atmosphere.'+'\033[1;93m',
               '\033[1;96m'+'Correct!\nThe uptake of atmospheric CO\u2082 by plants (photosynthesis) increases during spring and summer.\nAs a result, the lowest CO\u2082-concentration is observed in the beginning of autumn.'+'\033[1;96m']

############################################################################################################

#Create a class that includes all information of a question
class Question:
    
    #Set the values for all the object's attributes:
    def __init__(self, num, prompt, list_of_options, list_of_feedback, answer, widget_type):
        
        self.num = num
        self.prompt = prompt
        self.list_of_options = list_of_options
        self.list_of_feedback = list_of_feedback
        self.feedback_dict = {list_of_options[i]:list_of_feedback[i] for i in range(len(list_of_options))} #alt. dict(zip(q1_options, q1_feedback))
        self.answer = answer
        self.widget_type = widget_type
        
    #Function that returns the values of all the object's attributes:    
    def __str__(self):
        return 'Question number: {}\nPrompt: {}\nList of options: {}\nList of feedback: {}\nAnswer: {}\nWidget Type: {}'.format(self.num, self.prompt.replace('\n\n',''), self.list_of_options, self.list_of_feedback, self.answer, self.widget_type)
        
############################################################################################################

#Function that creates and returns an Image widget from an existing image file:
def add_image_widget(fullpath, imageFormat, im_width, im_hight):

    #Import modules:
    from ipywidgets import Image
    
    #Open file at given path:
    file = open(fullpath, "rb")
    
    #Read file:
    image = file.read()
    
    #Create image widget and set layout format:
    widget = Image(value=image,
                   format=imageFormat,
                   width=im_width,
                   height=im_hight)
    
    #Return widget
    return widget

############################################################################################################

#Function that creates and returns a widget for a given question object:
def create_q_widget(q):
    
    #Import modules:
    from ipywidgets import RadioButtons, Checkbox, Output, VBox, HBox
    from IPython.display import clear_output
    
    #Set widget style for description width:
    style = {'description_width': '80px'}
    
    #Initialize description output:
    description_out = Output()
    
    #Add quiz question to the description output:
    with description_out:
        print(q.prompt)
    
    #Check what type of widget should be created:
    if q.widget_type == 'RadioButtons':
        
        #Create RadioButtons-widget:
        w = RadioButtons(options = q.list_of_options,
                         description = ' ',
                         disabled = False)
        
        #Set widget width:
        w.layout.width = '370px'
        
        #Define feedback output:
        feedback = Output()
        
        #Open feedback object:
        with feedback:
            
            #Clear previous feedback:
            clear_output()
            
            #Print new feedback:
            print('')
    
        
        #Return widget in VBox:
        return VBox([description_out, w, feedback])
        
    
    #If the selected type of widget is ""Checkbox:
    elif q.widget_type == 'Checkbox':
        
        #Create list to store HBoxes:
        hbox_ls = []
        
        #Create a list of HBoxes, where every HBox includes a
        #Checkbox-widget and its corresponding feedback-output():
        for option in q.list_of_options:
            
            #Create widget:
            w = Checkbox(value=False, description=option, style=style, disabled=False)
            
            #Define feedback output:
            feedback = Output()
            
            #Open feedback object:
            with feedback:

                #Clear previous feedback:
                clear_output()

                #Print new feedback:
                print('')
            
            #Add Checkbox-widget and output()-widget with feedback to list:
            hbox_ls.append(HBox([w, feedback]))
        
        
        #Return all horizontal boxes in a vertical box including the prompt:
        return VBox([description_out] + hbox_ls)


    else:
        print('Question object has unknown widget type!')

############################################################################################################

def create_widget_form():
    
    #Import moduels:
    from ipywidgets import Button, Image, Output, VBox, HBox, Checkbox
    from IPython.display import clear_output
    
    #Create a question object for question 1:
    q1 = Question(1,
                  q1_prompt,
                  q1_options,
                  q1_feedback,
                  'Nitrogen (N\u2082)',
                  'RadioButtons')
    
    #Create a question object for question 2:
    q2 = Question(2,
                  q2_prompt,
                  q2_options,
                  q2_feedback,
                  ['Nitrous oxide (N\u2082O)', 'Carbon dioxide (CO\u2082)', 'Methane (CH\u2084)'],
                  'Checkbox')

    #Create a question object for question 3:
    q3 = Question(3,
                  q3_prompt,
                  q3_options,
                  q3_feedback,
                  ['Trees & vegetation', 'Reforestation', 'Oceanic photosynthesis'],
                  'Checkbox')
    
    #Create a question object for question 4:
    q4 = Question(4,
                  q4_prompt,
                  q4_options,
                  q4_feedback,
                  ['Forest fires', 'Volcanic eruptions', 'Decaying animal/plant remains', 'Burning fossil fuels'],
                  'Checkbox')
    
    #Create a question object for question 5:
    q5 = Question(5,
                  q5_prompt,
                  q5_options,
                  q5_feedback,
                  'Spring',
                  'RadioButtons')
    
    #Create a question object for question 6:
    q6 = Question(6,
                  q6_prompt,
                  q6_options,
                  q6_feedback,
                  'Photosynthesis',
                  'RadioButtons')




    #Call function to create widgets:
    w_q1 = create_q_widget(q1)
    w_q2 = create_q_widget(q2)
    w_q3 = create_q_widget(q3)
    w_q4 = create_q_widget(q4)
    w_q5 = create_q_widget(q5)
    w_q6 = create_q_widget(q6)
    
    
    
    #Create button widget (execution):
    button_exe = Button(description='Show results',
                        disabled=False,
                        button_style='danger', # 'success', 'info', 'warning', 'danger' or ''
                        tooltip='Click to display results',
                        icon='check')
    
    #Style button:
    button_exe.style.button_color = '#3973ac'
    button_exe.layout.width = '250px'
    button_exe.layout.margin = '50px 100px 40px 300px'
    
    #Create button widget (retake quiz):
    button_init = Button(description='   Try again',
                         disabled=False,
                         button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                         tooltip='Click to retake the quiz',
                         icon='repeat')
    
    #Style button:
    button_init.layout.width = '130px'
    button_init.layout.margin = '50px 50px 40px 100px'
    
    #Initialize quiz-form output:
    form_out = Output()
    
    #Initialize results output:
    results_out = Output()
    
    #Initialize icon output:
    icon_out = Output()
    
    
    #Open quiz-form object:
    with form_out:
        
        #Clear previous quiz:
        clear_output()
        
        #Display widgets:
        display(w_q1, w_q2, w_q3, w_q4, w_q5, w_q6, HBox([button_exe, button_init]), icon_out, results_out)
    
    
    #function that unchecks checked checkboxes:
    def uncheck_checkbox(q, w_q, i):
        
        #Set checkbox-value to False --> i.e. uncheck checked checkbox
        w_q.children[i].children[0].value=False
        
        
        
    
    
    #Function that deletes the feedback of a radiobutton-question:
    def del_feedback_radiobutton(q, w_q):
            
        #Open Output-object:
        with w_q.children[2]:
            
            #Delete current feedback-output:
            clear_output()
                
            #Print feedback:
            #print('')
                
                
                
    #Function that deletes the feedback of a checkbox-question:
    def del_feedback_checkbox(q, w_q, i):
            
        #Open Output-object:
        with w_q.children[i].children[1]:
            
            #Delete current feedback-output:
            clear_output()
        
    
    
    
    #Function that prints the number of correct answers:
    def show_grade(num_of_corr_ans, corr_ans_total):
        
        #Open results_out object:
        with results_out:
            
            #Clear previous feedback:
            clear_output()
                
            #Print new feedback:
            print('\033[1;96m'+'\t\t\t\t       ', num_of_corr_ans, '/', corr_ans_total, ' correct answers!'+'\033[1;96m')
    
    
    
    
    #Function that executes on button_click (reset quiz):
    def on_init_button_clicked(button_c):
        
        #Open results object:
        with results_out:
            
            #Delete previous results:
            clear_output()
            
            print('')
            
        
        #Open icon object:
        with icon_out:
            
            #Delete previous icon:
            clear_output()
            
            print('')
        
        
        #Open quiz-form object:
        with form_out:

            #Delete previous quiz:
            clear_output()
            
            #Uncheck checkboxes:
            [uncheck_checkbox(q2, w_q2, j) for j in range(1,len(w_q2.children))]
            [uncheck_checkbox(q3, w_q3, j) for j in range(1,len(w_q3.children))]
            [uncheck_checkbox(q4, w_q4, j) for j in range(1,len(w_q4.children))]
            
            #Reset radiobuttons:
            w_q1.children[1].value = 'Carbon dioxide (CO\u2082)'
            w_q5.children[1].value = 'Spring'
            w_q6.children[1].value = 'Livestock farming'
            
            
            #Delete feedback:
            del_feedback_radiobutton(q1, w_q1)
            [del_feedback_checkbox(q2, w_q2, i) for i in range(1,len(w_q2.children))]
            [del_feedback_checkbox(q3, w_q3, i) for i in range(1,len(w_q3.children))]
            [del_feedback_checkbox(q4, w_q4, i) for i in range(1,len(w_q4.children))]
            del_feedback_radiobutton(q5, w_q5)
            del_feedback_radiobutton(q6, w_q6)


            #Display widgets:
            display(w_q1, w_q2, w_q3, w_q4, w_q5, w_q6, HBox([button_exe, button_init]), icon_out, results_out)



    
    
    
    #Function that executes on button_click (calculate score):
    def on_exe_button_clicked(button_c):
        
        #Variable to count correct answers:
        count = 0
        
        #Variable to count wrong answers:
        false_ans_count = 0
        
        #Check answer of 1st question:
        if(w_q1.children[1].value == q1.answer):
            
            count = count + 1
            
            
        #Check answer of 5th question:
        if(w_q5.children[1].value == q5.answer):
             
            count = count + 1
            

        #Check answer of 6th question:
        if(w_q6.children[1].value == q6.answer):
             
            count = count + 1
            
            
        
        #Check answer of 1st question:
        if(w_q1.children[1].value != q1.answer):
            
            false_ans_count = false_ans_count + 1
            
            
        #Check answer of 5th question:
        if(w_q5.children[1].value != q5.answer):
             
            false_ans_count = false_ans_count + 1
            

        #Check answer of 6th question:
        if(w_q6.children[1].value != q6.answer):
             
            false_ans_count = false_ans_count + 1
            


        #Get a list of the values of the selected checkboxes:
        wq2_selected_boxes = [[w_q2.children[i].children[0].description,i] for i in range(1,len(w_q2.children)) if w_q2.children[i].children[0].value==True]
        wq3_selected_boxes = [[w_q3.children[i].children[0].description,i] for i in range(1,len(w_q3.children)) if w_q3.children[i].children[0].value==True]
        wq4_selected_boxes = [[w_q4.children[i].children[0].description,i] for i in range(1,len(w_q4.children)) if w_q4.children[i].children[0].value==True]
        
        
        #Get number of correct answers for checkbox-questions (q2, q3, q4):
        q2_corr_ans = len([val2[0] for val2 in wq2_selected_boxes if val2[0] in q2.answer])
        q3_corr_ans = len([val3[0] for val3 in wq3_selected_boxes if val3[0] in q3.answer])
        q4_corr_ans = len([val4[0] for val4 in wq4_selected_boxes if val4[0] in q4.answer])
        
        #Get number of false values of the selected checkboxes:
        q2_false_ans = len([val2[0] for val2 in wq2_selected_boxes if val2[0] not in q2.answer])
        q3_false_ans = len([val3[0] for val3 in wq3_selected_boxes if val3[0] not in q3.answer])
        q4_false_ans = len([val4[0] for val4 in wq4_selected_boxes if val4[0] not in q4.answer])
        
        
        #If the total number of correct answers for q2 is less than 3 --> wrong answer:
        if((q2_corr_ans - q2_false_ans) == 3):
            q2_ans = 1
        
        else:
            q2_ans = 0
        
        
        #If the total number of correct answers for q3 is less than 3 --> wrong answer:
        if((q3_corr_ans - q3_false_ans) == 3):
            q3_ans = 1
        
        else:
            q3_ans = 0
        
        
        #If the total number of correct answers for q4 is less than 4 --> wrong answer:
        if((q4_corr_ans - q4_false_ans) == 4):
            q4_ans = 1
        
        else:
            q4_ans = 0
        
        
        #Add the total number of correct answers (from the checkbox questions) to count:
        score = count + q2_ans + q3_ans + q4_ans

  
        #Check number of correct answers:
        if(score<3):            
            
            
            #Show badge:
            with icon_out:
                
                #Delete previous image widget:
                clear_output()
                
                #Create image widget:
                black_fp = add_image_widget('gifs/oops.gif', 'gif', 400, 600)
                
                #Define the layout of the image widget:
                black_fp.layout.margin = '50px 10px 40px 300px'
                
                #Display image widget:
                display(black_fp)
                
            
            #Show grade:
            show_grade(score, 6)

            
        #Check number of correct answers:   
        elif(score>2 and score<4):
            
            #Show badge:
            with icon_out:
                
                #Delete previous image widget:
                clear_output()
                
                #Create image widget:
                orange_fp = add_image_widget('gifs/novisch.gif', 'gif', 400, 600)
                
                #Define the layout of the image widget:
                orange_fp.layout.margin = '50px 100px 40px 300px'
                
                #Display image widget:
                display(orange_fp)
                
            
            #Show grade:
            show_grade(score, 6)
                
            
        #Check number of correct answers:  
        elif(score>3 and score<6):
            
            #Show badge:
            with icon_out:
                
                #Delete previous image widget:
                clear_output()
                
                #Create image widget:
                green_fp = add_image_widget('gifs/climate_aware.gif', 'gif', 400, 600)
                
                #Define the layout of the image widget:
                green_fp.layout.margin = '50px 100px 40px 300px'
                
                #Display image widget:
                display(green_fp)
            
            
            #Show grade:
            show_grade(score, 6)
                
         
                
        #Check number of correct answers:    
        else:
            
            #Show badge:
            with icon_out:
                
                #Delete previous image widget:
                clear_output()

                #Create image widget:
                clim_champ = add_image_widget('gifs/champion.gif', 'gif', 400, 600)
                
                #Define the layout of the image widget:
                clim_champ.layout.margin = '50px 100px 40px 300px'
                
                #Display image widget:
                display(clim_champ)
                
            
            #Show grade:
            show_grade(score, 6)
            
        
        
        ##### Feedback - Radiobuttons ######
        #Function that returns a feedback-output for a given question-object
        #and question-widget:
        def return_feedback_radiobutton(q, w_q):
            
            #Open Output-object:
            with w_q.children[2]:
                
                #Delete current feedback-output:
                clear_output()
                
                #Print feedback:
                print(q.feedback_dict[w_q.children[1].value])

        
        ###### Feedback - Checkboxes #####
        #Function that returns a feedback-output for a given question-object,
        #question-widget and checkbox number (i.e. order in question-widget):
        def return_feedback_checkbox(q, w_q, i):
            
            #Open Output-object:
            with w_q.children[i].children[1]:
            
                #Delete current feedback-output:
                clear_output()

                #If current checkbox is checked:
                if(w_q.children[i].children[0].value):

                    #Print feedback:
                    print(q.feedback_dict[w_q.children[i].children[0].description])
                
                #If current checkbox is not checked:
                else:
                    
                    #Print feedback:
                    print('')
                    
        
        
        
                
        #Print feedback for question 1:  
        return_feedback_radiobutton(q1, w_q1)
            
        #Print Feedback for question 2:
        [return_feedback_checkbox(q2, w_q2, i) for i in range(1,len(w_q2.children))]
        
        #Print Feedback for question 3:
        [return_feedback_checkbox(q3, w_q3, i) for i in range(1,len(w_q3.children))]
        
        #Print Feedback for question 4:
        [return_feedback_checkbox(q4, w_q4, i) for i in range(1,len(w_q4.children))]
        
        #Print feedback for question 5:  
        return_feedback_radiobutton(q5, w_q5)
        
        #Print feedback for question 6:  
        return_feedback_radiobutton(q6, w_q6)
 
 
            
    #Call function on button_click-event (calculate score):
    button_exe.on_click(on_exe_button_clicked)
    
    #Call function on button_click-event (retake quiz):
    button_init.on_click(on_init_button_clicked)

        
    #Display results:
    display(form_out)
    
############################################################################################################

    

