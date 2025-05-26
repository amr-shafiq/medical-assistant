using UnityEngine;

public class CharacterAnimationController : MonoBehaviour
{
    public GameObject character;  
    public Animator animator;     
    

    void Start()
    {
        if (animator == null)
        {
            animator = GetComponent<Animator>();
        }
    }

    public void StartTalking()
    {
        if (animator != null)
        {
            animator.SetBool("IsTalking", true);
            animator.Update(0); 
            Debug.Log("IsTalking set to TRUE. Character is now talking.");
        }
        else
        {
            Debug.LogError("Animator is NULL in StartTalking!");
        }
    }

    public void StopTalking()
    {
        if (animator != null)
        {
            animator.SetBool("IsTalking", false);
            animator.Update(0);
            Debug.Log("IsTalking set to FALSE. Transitioning to 'Idle' state.");
        }
        else
        {
            Debug.LogError("Animator is NULL in StopTalking!");
        }
    }

    public void LogCurrentState()
    {
        if (animator != null)
        {
            AnimatorStateInfo currentState = animator.GetCurrentAnimatorStateInfo(0);
            Debug.Log($"Current animation state: {currentState.fullPathHash}");
        }
    }
}








